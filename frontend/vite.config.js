import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

/**
 * 多页应用（MPA）配置。
 *
 * 官网的五个导航项各自对应一个独立的根页面（index / product / factory /
 * custom / contact），而不是单页应用里的路由切换，因此：
 *   - 每个页面是独立的 HTML 入口，构建产物也是多个 HTML 文件
 *   - appType 设为 'mpa'，开发服务器才不会把未知路径回落到 index.html
 *   - base 在构建时指向 Django 的静态目录，让产物引用能正确解析
 */
const PAGES = ['index', 'product', 'factory', 'custom', 'contact']

/**
 * 开发服务器的 clean URL 重写。
 *
 * 导航使用站点根路径（/product/），但开发时真实文件是 product.html。
 * 这个插件把 /product/ 映射到 /product.html，让开发模式与 Django 生产模式
 * 的访问地址保持一致，无需在两套地址之间来回切换。
 */
function cleanUrlPlugin() {
  return {
    name: 'mpa-clean-url',
    configureServer(server) {
      // 用返回函数的形式注册，确保在 Vite 内部中间件之前处理
      return () => {
        server.middlewares.use((req, _res, next) => {
          const url = req.url
          if (!url || url === '/' || url.includes('.') || url.startsWith('/@')) {
            next()
            return
          }
          const name = url.replace(/^\/|\/$/g, '')
          if (PAGES.includes(name)) {
            req.url = `/${name}.html`
          }
          next()
        })
      }
    },
  }
}

export default defineConfig(({ command }) => ({
  plugins: [vue(), cleanUrlPlugin()],

  // 构建产物由 Django 托管在 /static/frontend/ 下，base 需与之对应
  base: command === 'build' ? '/static/frontend/' : '/',

  // 多页模式：开发服务器按真实文件路径提供页面
  appType: 'mpa',

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    port: 5173,
    // 显式绑定 IPv4。默认监听 [::1]（IPv6 回环），
    // 用 127.0.0.1 访问会连不上，指定 127.0.0.1 可避免该问题
    host: '127.0.0.1',
    // 开发模式下把 /api 请求转发给 Django 后端，避免跨域
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    // 构建产物输出到 Django 应用的静态目录，由 Django 统一托管
    outDir: '../web/static/frontend',
    emptyOutDir: true,
    rollupOptions: {
      input: Object.fromEntries(
        PAGES.map((name) => [name, fileURLToPath(new URL(`./${name}.html`, import.meta.url))]),
      ),
    },
  },
}))
