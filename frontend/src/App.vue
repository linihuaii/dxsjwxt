<script setup>
import { ref } from 'vue'
import logo from './assets/logo.svg'
import SchedulePreview from './SchedulePreview.vue'
import { submitContact } from './api/index.js'

const path = location.pathname.split('/').filter(Boolean)[0] || 'index'
const page = path.replace('.html', '')
const productUrl = 'https://152.136.97.64/'
const menu = ref(false)
const sending = ref(false)
const message = ref('')
const form = ref({ name: '', phone: '', city: '', description: '' })
const nav = [
  { id: 'index', label: '首页', href: '/' },
  { id: 'product', label: '功能介绍', href: '/product/' },
  { id: 'factory', label: '系统设计', href: '/factory/' },
  { id: 'custom', label: '使用流程', href: '/custom/' },
  { id: 'contact', label: '项目反馈', href: '/contact/' },
]
const features = [
  {
    id: 'import',
    icon: '▦',
    title: '添加与导入课程',
    summary: '手动添加单门课，或用 CSV 模板一次导入多门课程。',
    description: '填写课程名称、教师、地点、星期、起止节次和起止周。已有课表时，可以从产品中下载 CSV 模板，填好后批量导入。',
    details: ['手动添加、编辑或删除课程', '从产品下载 CSV 模板，按模板填写后导入', '为课程选择颜色，也可设置导入时的默认颜色'],
  },
  {
    id: 'view',
    icon: '◷',
    title: '周课表与今日课程',
    summary: '切换教学周，按课程、教师或地点搜索，随时查看当天安排。',
    description: '周课表按星期和节次展示选中教学周的课程，旁边的「今天的课程」按节次列出当天安排。可在「节次时间」中按学校作息填写每节课的上下课时间。',
    details: ['切换教学周，点击课表中的课程查看或编辑', '按课程名、教师或地点搜索', '授权浏览器通知后，打开课序时可收到当天课程提醒'],
  },
  {
    id: 'assist',
    icon: '✳',
    title: '课程统计与课程助手',
    summary: '用统计了解课程分布，也可以向课程助手提问。',
    description: '课程统计展示课程总数、本周课程、本周总节次、授课教师和每日课程分布。课程助手可以回答课程内容、学习方法等问题。',
    details: ['本周统计随所选周次与搜索条件变化', '在课程助手中输入课程名称或具体学习问题', '通过「模型设置」使用服务器默认配置或填写兼容接口'],
  },
]
const steps = [
  { title: '登录或注册', description: '点击「进入产品」。有账号直接登录，首次使用可以在登录页切换到注册。' },
  { title: '添加课程或导入 CSV', description: '打开「我的课表」，逐门添加课程，或下载产品内的 CSV 模板，填写后批量导入。' },
  { title: '按周查课，自定义节次', description: '用切周按钮查看不同教学周，或按课程、教师、地点搜索。按需设置节次时间和浏览器通知。' },
  { title: '查看统计，向课程助手提问', description: '在「课程统计」查看课程分布与节次，在「课程助手」输入想了解的课程或学习问题。' },
]

async function send() {
  sending.value = true
  const result = await submitContact(form.value)
  message.value = result.message || (result.ok ? '提交成功' : '提交失败，请检查填写内容。')
  if (result.ok) form.value = { name: '', phone: '', city: '', description: '' }
  sending.value = false
}
</script>

<template>
  <header class="header">
    <div class="nav-wrap">
      <a class="brand" href="/">
        <img :src="logo" alt="">
        <span><b>课序</b><small>COURSE ORDER</small></span>
      </a>
      <button class="menu-btn" type="button" aria-controls="site-nav" :aria-expanded="menu"
        :aria-label="menu ? '关闭主导航' : '展开主导航'" @click="menu = !menu">☰</button>
      <nav id="site-nav" :class="{ open: menu }" aria-label="主导航">
        <a v-for="item in nav" :key="item.id" :href="item.href"
          :class="{ active: page === item.id }" :aria-current="page === item.id ? 'page' : undefined">{{ item.label }}</a>
      </nav>
      <a class="nav-cta" :href="productUrl">进入产品</a>
    </div>
  </header>

  <main v-if="page === 'index'">
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-copy">
          <div class="eyebrow light"><span></span>课序 · 大学生课表系统</div>
          <h1>让每一周，<br><em>都有序可循。</em></h1>
          <p>在课序建立你的大学课表，按周查看课程和今天的安排。你也可以导入 CSV、查看课程统计，或者向课程助手提问。</p>
          <div class="actions">
            <a class="button lime" :href="productUrl">进入产品</a>
            <a class="text-link light-link" href="/product/">查看产品功能</a>
          </div>
          <p class="hero-access">打开课序后，登录或注册即可建立自己的课表。</p>
        </div>
        <SchedulePreview />
      </div>
    </section>

    <section class="features section">
      <div class="section-top">
        <h2>一张课表，管好一学期</h2>
        <p>从开学录入课程，到每天查课，再到回顾每周安排。</p>
      </div>
      <div class="feature-grid">
        <article v-for="feature in features" :key="feature.id">
          <div class="icon" aria-hidden="true">{{ feature.icon }}</div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.summary }}</p>
          <a :href="'/product/#' + feature.id">查看{{ feature.title }}</a>
        </article>
      </div>
    </section>

    <section class="statement section">
      <h2>从第一门课开始</h2>
      <div>
        <p>打开课序，手动添加一门课，或用模板把整份课表导入。</p>
        <div class="actions section-actions">
          <a class="button dark" :href="productUrl">进入产品</a>
          <a class="text-link" href="/custom/">查看使用流程</a>
        </div>
      </div>
    </section>
  </main>

  <main v-else-if="page === 'product'">
    <section class="page-hero">
      <div class="section-label">产品功能</div>
      <h1>课表、统计与助手，<br><em>都在课序。</em></h1>
      <p>从导入课表到日常查课，了解你可以在课序中完成哪些操作。</p>
      <div class="actions">
        <a class="button lime" :href="productUrl">进入产品</a>
        <a class="text-link light-link" href="/custom/">查看使用流程</a>
      </div>
    </section>
    <section v-for="(feature, index) in features" :id="feature.id" :key="feature.id"
      class="section detail-row" :class="{ tinted: index % 2 === 1 }">
      <h2>{{ feature.title }}</h2>
      <div>
        <p>{{ feature.description }}</p>
        <ul class="mini-list feature-details">
          <li v-for="detail in feature.details" :key="detail">{{ detail }}</li>
        </ul>
      </div>
    </section>
  </main>

  <main v-else-if="page === 'factory'">
    <section class="page-hero">
      <div class="section-label">系统设计</div>
      <h1>课程数据如何<br><em>变成一张课表</em></h1>
      <p>课序用星期、节次和周次组织课程，把同一份课程数据用于课表、今日课程和统计。</p>
    </section>
    <section class="section">
      <div class="section-top">
        <h2>从录入到展示</h2>
      </div>
      <div class="architecture">
        <div>
          <h3>课程录入</h3>
          <p>手动添加课程或通过 CSV 导入，记录一门课的星期、节次和起止周。</p>
        </div>
        <b aria-hidden="true">↓</b>
        <div>
          <h3>按周筛选</h3>
          <p>根据所选教学周、课程起止周和搜索条件筛选课程。</p>
        </div>
        <b aria-hidden="true">↓</b>
        <div>
          <h3>课表与统计</h3>
          <p>把筛选结果排进周课表，并计算本周的课程数、节次和每日分布。</p>
        </div>
      </div>
    </section>
    <section class="statement section">
      <h2>课程与设置</h2>
      <div>
        <p>登录后管理自己的课程。节次时间和自定义模型设置保存在当前浏览器，课程提醒使用浏览器通知。</p>
        <a class="button outline" href="/custom/">查看使用流程</a>
      </div>
    </section>
  </main>

  <main v-else-if="page === 'custom'">
    <section class="page-hero">
      <div class="section-label">使用流程</div>
      <h1>从注册到<br><em>排好第一周</em></h1>
      <p>打开课序，沿着下面四个步骤建立并使用自己的课表。</p>
      <div class="actions">
        <a class="button lime" :href="productUrl">进入产品</a>
      </div>
    </section>
    <section class="section">
      <ol class="journey">
        <li v-for="(step, index) in steps" :key="step.title">
          <span aria-hidden="true">{{ index + 1 }}</span>
          <h3>{{ step.title }}</h3>
          <p>{{ step.description }}</p>
        </li>
      </ol>
    </section>
    <section class="notice section">
      <h2>有使用反馈？</h2>
      <p>如果遇到导入或查看课程的问题，欢迎把使用场景告诉项目组。</p>
      <a class="button dark" href="/contact/">留下项目反馈</a>
    </section>
  </main>

  <main v-else>
    <section class="page-hero">
      <div class="section-label">项目反馈</div>
      <h1>好的课表体验，<br><em>从你的想法开始。</em></h1>
      <p>对课程管理有什么想法？欢迎向项目组留下反馈。</p>
    </section>
    <section class="section contact-layout">
      <div>
        <h2>一起把课序<br>做得更好。</h2>
        <p>无论是课表导入、课程查看，还是日常使用中的细节，都欢迎告诉我们。</p>
      </div>
      <form @submit.prevent="send">
        <label>称呼 <span>*</span><input v-model="form.name" required maxlength="50" placeholder="如何称呼你？"></label>
        <label>联系电话 <span>*</span><input v-model="form.phone" required maxlength="20" placeholder="请输入联系电话"></label>
        <label>所在城市<input v-model="form.city" maxlength="50" placeholder="选填"></label>
        <label>你的建议<textarea v-model="form.description" rows="5" placeholder="说说你的想法或使用场景"></textarea></label>
        <button class="button dark" :disabled="sending">{{ sending ? '正在提交…' : '提交反馈' }}</button>
        <p class="form-message" role="status">{{ message }}</p>
      </form>
    </section>
  </main>

  <footer>
    <div class="footer-top">
      <a class="brand footer-brand" href="/"><img :src="logo" alt=""><span><b>课序</b><small>COURSE ORDER</small></span></a>
      <div class="footer-links">
        <a v-for="item in nav" :key="item.id" :href="item.href">{{ item.label }}</a>
        <a :href="productUrl">进入产品</a>
      </div>
    </div>
    <div class="footer-bottom"><span>© 2026 课序 · 大学生课表系统项目</span></div>
  </footer>
</template>
