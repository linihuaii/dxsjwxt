<script setup>
import { computed, ref } from 'vue'

const week = ref(3)
const lastWeek = 16
const days = ['周一', '周二', '周三', '周四', '周五']
const periods = ['1–2 节', '3–4 节', '5–6 节']
const lessons = [
  { day: '周一', period: '1–2 节', name: '软件工程', room: 'A201', start: 1, end: 16, color: 'mint' },
  { day: '周二', period: '1–2 节', name: '大学英语', room: 'B304', start: 1, end: 16, color: 'peach' },
  { day: '周三', period: '3–4 节', name: '数据结构', room: '实验楼', start: 2, end: 12, color: 'blue' },
  { day: '周四', period: '3–4 节', name: '高等数学', room: 'C105', start: 1, end: 16, color: 'cream' },
  { day: '周五', period: '5–6 节', name: '大学物理', room: 'A406', start: 3, end: 16, color: 'lavender' },
]
const visibleLessons = computed(() => lessons.filter(lesson => lesson.start <= week.value && week.value <= lesson.end))
const lessonsBySlot = computed(() => Object.fromEntries(
  visibleLessons.value.map(lesson => [lesson.period + lesson.day, lesson]),
))
</script>

<template>
  <figure class="schedule-preview">
    <figcaption>交互预览 · 示例课表</figcaption>
    <div class="schedule-preview-heading">
      <div>
        <h2>我的课表</h2>
        <p>工作日 · {{ visibleLessons.length }} 门课程</p>
      </div>
      <div class="week-control">
        <button type="button" :disabled="week === 1" aria-label="示例课表上一周" @click="week--">‹</button>
        <b aria-live="polite">第 {{ week }} 周</b>
        <button type="button" :disabled="week === lastWeek" aria-label="示例课表下一周" @click="week++">›</button>
      </div>
    </div>
    <table aria-label="工作日示例课表">
      <thead>
        <tr>
          <th scope="col">节次</th>
          <th v-for="day in days" :key="day" scope="col">{{ day }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="period in periods" :key="period">
          <th scope="row">{{ period }}</th>
          <td v-for="day in days" :key="day">
            <div v-if="lessonsBySlot[period + day]" class="preview-lesson" :class="lessonsBySlot[period + day].color">
              <strong>{{ lessonsBySlot[period + day].name }}</strong>
              <span>{{ lessonsBySlot[period + day].room }}</span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </figure>
</template>

<style scoped>
.schedule-preview {
  min-width: 0;
  margin: 0;
  padding: clamp(12px, 2.1vw, 28px);
  color: #203d35;
  background: #f7f8f1;
  border: 1px solid #e3eadf;
  border-radius: 12px;
  box-shadow: 0 24px 60px #0b272160;
}

figcaption {
  color: #516c5f;
  font-size: .8125rem;
  font-weight: 700;
}

.schedule-preview-heading {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin: 13px 0 20px;
}

h2 {
  margin: 0 0 4px;
  font-size: 1.45rem;
  line-height: 1.25;
}

p {
  margin: 0;
  color: #516c5f;
  font-size: .8125rem;
}

.week-control {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .8125rem;
  white-space: nowrap;
}

.week-control button {
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  color: #203d35;
  background: #e7eee2;
  border: 1px solid #d8e4d6;
  border-radius: 50%;
  font-size: 1.25rem;
}

.week-control button:not(:disabled):hover {
  background: #d5e8c7;
}

.week-control button:disabled {
  cursor: default;
  opacity: .45;
}

table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

th {
  color: #486458;
  font-size: .8125rem;
}

th:first-child {
  width: 3.25rem;
  padding-right: 4px;
  text-align: left;
}

thead th {
  padding-bottom: 10px;
}

td, tbody th {
  height: 67px;
  border-top: 1px solid #dde7d9;
}

td {
  padding: 3px 2px;
  vertical-align: top;
}

.preview-lesson {
  display: flex;
  min-height: 60px;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  padding: 4px;
  border-radius: 5px;
  font-size: .8125rem;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.preview-lesson span {
  font-size: .75rem;
}

.mint { background: #d9edbd; }
.peach { background: #f6dfcb; }
.cream { background: #f4ebc9; }
.blue { background: #d7e9e6; }
.lavender { background: #e6dff1; }

@media (max-width: 420px) {
  th:first-child {
    width: 2.45rem;
  }
}
</style>
