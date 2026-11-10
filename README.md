# 课序 大学生课表系统项目展示网站

采用 Vue 3 + Vite 多页面前端、Django + Django REST Framework 后端和 SQLite 数据库。网站介绍需求文档中的目标系统；首页课表为示例，目标系统的课程管理、学校导入、提醒及 AI 尚未在本网站实现。反馈表单写入本地数据库，可通过 Django 管理后台查看。

## 启动

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

访问 http://127.0.0.1:8000/ ，后台为 http://127.0.0.1:8000/admin/ 。反馈后台需要自行创建管理员。

修改前端后，在 `frontend` 目录运行 `npm install` 和 `npm run build`，产物输出至 `web/static/frontend/`，由 Django 提供。开发模式可用 `npm run dev`，API 代理到本机 8000 端口。

## 标识

`brand/logo.svg` 是专为课序设计的矢量标识：日历轮廓代表课表，勾选符号代表清晰核对。前端使用同源 SVG。

本项目默认配置仅供本地开发；公开部署前应配置密钥、关闭 DEBUG 并设置允许的主机和静态文件服务。
