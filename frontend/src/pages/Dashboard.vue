<template>
  <div>
    <div class="page-head">
      <h2>运营概览</h2>
      <p class="sub">销售额、订单与识别准确率总览，以及近 7/30 天趋势</p>
    </div>
    <div class="cards">
      <div class="card acc-blue"><div class="card-label">总销售额</div><div class="card-value">¥{{ ov.total_sales?.toFixed(2) ?? '-' }}</div></div>
      <div class="card acc-green"><div class="card-label">总订单数</div><div class="card-value">{{ ov.total_orders ?? '-' }}</div></div>
      <div class="card acc-purple"><div class="card-label">识别准确率（演示口径）</div><div class="card-value">{{ ov.accuracy == null ? '-' : ov.accuracy + '%' }}</div></div>
    </div>
    <div class="grid2">
      <div class="panel">
        <h3>近 {{ days }} 天销售额曲线</h3>
        <div class="day-switch">
          <button class="btn small" :class="{ primary: days === 7 }" @click="setDays(7)">近7天</button>
          <button class="btn small" :class="{ primary: days === 30 }" @click="setDays(30)">近30天</button>
        </div>
        <div ref="trendRef" class="chart"></div>
      </div>
      <div class="panel">
        <h3>品类销售占比</h3>
        <div ref="pieRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const ov = ref({})
const days = ref(7)
const trendRef = ref(null)
const pieRef = ref(null)
let trendChart = null
let pieChart = null

async function load() {
  const [o, t, c] = await Promise.all([
    api.get('/stats/overview'),
    api.get(`/stats/trend?days=${days.value}`),
    api.get('/stats/category'),
  ])
  ov.value = o.data
  trendChart?.setOption({
    xAxis: { type: 'category', data: t.data.map((x) => x.date.slice(5)) },
    yAxis: { type: 'value', name: '销售额(元)' },
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.15 }, data: t.data.map((x) => x.amount) }],
  })
  pieChart?.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#9fb3c8' } },
    series: [{
      type: 'pie', radius: ['35%', '65%'], center: ['50%', '45%'],
      label: { color: '#dce6f0' },
      data: c.data.length ? c.data : [{ name: '暂无销售', value: 1, itemStyle: { color: '#33455c' } }],
    }],
  })
}

function setDays(d) { days.value = d; load() }
function onResize() { trendChart?.resize(); pieChart?.resize() }

onMounted(() => {
  trendChart = echarts.init(trendRef.value)
  pieChart = echarts.init(pieRef.value)
  load()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  trendChart?.dispose(); pieChart?.dispose()
})
</script>
