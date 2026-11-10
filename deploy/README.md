# 腾讯云部署指南

本指南将展示网站部署到一台 Ubuntu 轻量应用服务器：Nginx 提供静态资源并代理 Gunicorn，Django 使用单机 SQLite 存储反馈。网站展示的是课表系统需求，课程管理和 AI 等目标功能本身尚未实现。本指南使用域名和 HTTPS；需要一台有公网 IPv4 的服务器、可管理的域名，以及能 SSH 登录并使用 sudo 的账户。

## 1. 准备云资源

1. 创建腾讯云轻量应用服务器，选择受支持的 Ubuntu 系统。确认系统可提供 Python 3.13 与 venv；以下使用 `python3.13`，实际镜像不可用时请先按 Ubuntu 官方方式安装兼容版本。确保公网 IP 可用。
2. 在腾讯云实例防火墙开放 TCP 80 和 443；TCP 22 仅对管理者的可信 IP 开放。系统内如启用 UFW 等防火墙，也需放行相应端口。不要开放 8000 端口。
3. 将域名的 A 记录指向公网 IP。将下文 `example.com` 替换成自己的域名；如果还使用其他域名，需同时配置 DNS、Nginx 和环境变量。
4. 域名指向中国境内服务器时，先按腾讯云要求完成 ICP 备案；纯公网 IP 测试和非中国境内资源的要求请参照腾讯云现行规定。HTTPS 正式访问建议使用有效域名。

## 2. 安装软件并拉取项目

通过 SSH 登录服务器，以下命令在服务器运行。Ubuntu 软件仓库的 Python 版本因镜像而异，请先确保 `python3.13 --version`、`python3.13 -m venv --help` 可用。

```bash
sudo apt update
sudo apt install -y git nginx certbot python3-certbot-nginx
sudo useradd --system --home-dir /opt/course-order --shell /usr/sbin/nologin courseorder
sudo git clone https://github.com/linihuaii/-.git /opt/course-order
sudo chown -R courseorder:courseorder /opt/course-order
sudo install -d -o courseorder -g courseorder -m 750 /var/lib/course-order
cd /opt/course-order
sudo -u courseorder python3.13 -m venv .venv
sudo -u courseorder .venv/bin/python -m pip install -r requirements-production.txt
```

若仓库是私有仓库，先为服务器配置有只读权限的 GitHub 访问方式。不要把令牌写入仓库或命令历史。首次安装后确认依赖安装成功；若指定版本在服务器的包源中不可用，需先解决版本兼容问题。

## 3. 创建生产环境配置和数据库

```bash
sudo install -o root -g root -m 600 deploy/production.env.example /etc/course-order.env
sudo nano /etc/course-order.env
```

填写 `DJANGO_SECRET_KEY`（使用下面命令生成独立随机值）、实际域名和 `https://` 开头的 CSRF 来源。不要沿用示例值或开发配置中的密钥，不要将配置文件提交到 Git。环境文件由 systemd 读取，限 root 访问。密钥包含特殊字符时保留在一行；生成值使用字母数字以便与 systemd 环境文件兼容。

```bash
/opt/course-order/.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
```

在当前 shell 中临时导入配置，执行迁移和静态文件收集。下面的 `sudo` 通过 `systemd-run` 使用同一环境文件运行命令，以避免公开密钥：

```bash
sudo systemd-run --wait --pipe --collect --uid=courseorder --gid=courseorder \
  --working-directory=/opt/course-order -p EnvironmentFile=/etc/course-order.env \
  /opt/course-order/.venv/bin/python manage.py migrate --noinput
sudo systemd-run --wait --pipe --collect --uid=courseorder --gid=courseorder \
  --working-directory=/opt/course-order -p EnvironmentFile=/etc/course-order.env \
  /opt/course-order/.venv/bin/python manage.py collectstatic --noinput
sudo systemd-run --wait --pipe --collect --uid=courseorder --gid=courseorder \
  --working-directory=/opt/course-order -p EnvironmentFile=/etc/course-order.env \
  /opt/course-order/.venv/bin/python manage.py check --deploy
```

`check --deploy` 会提示 HSTS 尚未启用，以及 X-Frame-Options 使用 SAMEORIGIN 而非 DENY。前者可在确认 HTTPS 稳定并了解影响后启用；后者用于兼容 SimpleUI 后台的同源 iframe。为交互式创建后台管理员，使用下面命令读取环境文件并运行（请勿把密码写进命令）：

```bash
sudo systemd-run --wait --pty --collect --uid=courseorder --gid=courseorder \
  --working-directory=/opt/course-order -p EnvironmentFile=/etc/course-order.env \
  /opt/course-order/.venv/bin/python manage.py createsuperuser
```

## 4. 启动服务并启用 HTTPS

```bash
sudo cp /opt/course-order/deploy/course-order.service /etc/systemd/system/course-order.service
sudo systemctl daemon-reload
sudo systemctl enable --now course-order
sudo systemctl status course-order --no-pager
sudo cp /opt/course-order/deploy/nginx.conf /etc/nginx/sites-available/course-order
sudo nano /etc/nginx/sites-available/course-order
```

将 Nginx 文件中的 `example.com` 替换成真实域名，然后启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/course-order /etc/nginx/sites-enabled/course-order
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d example.com
sudo certbot renew --dry-run
```

Certbot 会修改 Nginx 配置以启用证书和 HTTPS。执行前确保域名解析、80 端口和备案条件均已满足；按交互提示选择 HTTP 跳转 HTTPS。正式配置始终启用 Django 的 HTTPS 重定向和安全 Cookie，因此证书配置完成前 HTTP 不能作为正常网站使用。证书申请失败时查看 Certbot 报错，勿关闭安全设置来作为正式部署。

确认网站、静态资源、导航和反馈提交，以及 `https://example.com/admin/` 登录可用：

```bash
curl -I https://example.com/
sudo journalctl -u course-order -n 100 --no-pager
sudo nginx -t
```

当前服务仅监听 `127.0.0.1:8000`，由 Nginx 重写 `X-Forwarded-Proto`；不要将 Gunicorn 端口暴露到公网，否则客户端可能伪造该头。Django 日志与 Nginx 日志不要记录密钥或用户敏感信息。

## 5. 后续更新与备份

更新前先备份数据库；SQLite 的数据库文件在 `/var/lib/course-order/db.sqlite3`，不在 Git 仓库中。使用 SQLite 在线备份 API 制作一致快照，例如：

```bash
sudo -u courseorder /opt/course-order/.venv/bin/python -c "import sqlite3; s=sqlite3.connect('/var/lib/course-order/db.sqlite3'); d=sqlite3.connect('/var/lib/course-order/backup.sqlite3'); s.backup(d); d.close(); s.close()"
```

将快照复制到受保护的异地位置并定期演练恢复。备份包含反馈个人信息，应限制访问。每次更新：

```bash
cd /opt/course-order
sudo -u courseorder git pull --ff-only
sudo -u courseorder .venv/bin/python -m pip install -r requirements-production.txt
sudo systemd-run --wait --pipe --collect --uid=courseorder --gid=courseorder --working-directory=/opt/course-order -p EnvironmentFile=/etc/course-order.env /opt/course-order/.venv/bin/python manage.py migrate --noinput
sudo systemd-run --wait --pipe --collect --uid=courseorder --gid=courseorder --working-directory=/opt/course-order -p EnvironmentFile=/etc/course-order.env /opt/course-order/.venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart course-order
sudo systemctl status course-order --no-pager
```

如修改 Vue 源码，先在开发环境执行 `npm ci` 和 `npm run build`，提交 `web/static/frontend/` 构建产物后再更新服务器。变更 systemd 或 Nginx 示例时，需要重新复制配置、检查并重载。多个进程下默认内存限流计数不会共享；如果需要严格全局限流，应配置共享缓存。单机 SQLite 适合小规模展示，不能替代高并发数据库或备份方案。
