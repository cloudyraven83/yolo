<template>
  <div>
    <div class="page-head">
      <h2>预警与记录</h2>
      <p class="sub">低库存/售空预警处理，以及交易与识别记录明细</p>
    </div>
    <div class="panel">
      <h3>补货预警</h3>
      <div class="table-wrap">
      <table class="table">
        <thead><tr><th>时间</th><th>货道</th><th>商品</th><th>类型</th><th>内容</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="a in alerts" :key="a.id">
            <td>{{ fmt(a.created_at) }}</td>
            <td>{{ a.shelf_no }}</td>
            <td>{{ a.product }}</td>
            <td>{{ a.type === 'empty' ? '售空' : '低库存' }}</td>
            <td>{{ a.message }}</td>
            <td><span class="badge" :class="a.status === 'open' ? 'open' : 'idle'">{{ a.status === 'open' ? '待处理' : '已处理' }}</span></td>
            <td>
              <button v-if="a.status === 'open'" class="btn small" @click="resolve(a)">标记处理</button>
            </td>
          </tr>
          <tr v-if="!alerts.length"><td colspan="7">暂无预警</td></tr>
        </tbody>
      </table>
      </div>
    </div>

    <div class="panel">
      <h3>交易与识别记录</h3>
      <div class="table-wrap">
      <table class="table">
        <thead><tr><th>会话</th><th>开始</th><th>结束</th><th>金额</th><th>状态</th><th>详情</th></tr></thead>
        <tbody>
          <template v-for="s in sessions" :key="s.id">
            <tr>
              <td>#{{ s.id }}</td>
              <td>{{ fmt(s.started_at) }}</td>
              <td>{{ fmt(s.ended_at) }}</td>
              <td>¥{{ s.total_amount.toFixed(2) }}</td>
              <td><span class="badge" :class="s.status === 'paid' ? 'idle' : s.status === 'open' ? 'open' : ''">
                {{ { open: '识别中', closed: '待支付', paid: '已支付' }[s.status] }}</span></td>
              <td><button class="btn small" @click="toggle(s)">{{ expanded === s.id ? '收起' : '展开' }}</button></td>
            </tr>
            <tr v-if="expanded === s.id && detail">
              <td colspan="6">
                <div class="detail">
                  <div>
                    <h4>成交明细</h4>
                    <table class="table">
                      <thead><tr><th>商品</th><th>数量</th><th>单价</th><th>小计</th></tr></thead>
                      <tbody>
                        <tr v-for="(it, i) in detail.items" :key="i">
                          <td>{{ it.name }}</td><td>{{ it.quantity }}</td>
                          <td>¥{{ it.unit_price.toFixed(2) }}</td><td>¥{{ it.subtotal.toFixed(2) }}</td>
                        </tr>
                        <tr v-if="!detail.items.length"><td colspan="4">无成交</td></tr>
                      </tbody>
                    </table>
                  </div>
                  <div>
                    <h4>识别记录明细（最近 {{ detail.logs.length }} 条）</h4>
                    <table class="table">
                      <thead><tr><th>时间</th><th>通道</th><th>结果</th><th>置信度</th><th>计入成交</th></tr></thead>
                      <tbody>
                        <tr v-for="(l, i) in detail.logs" :key="i">
                          <td>{{ fmt(l.ts) }}</td><td>{{ l.provider }}</td><td>{{ l.label }}</td>
                          <td>{{ l.confidence }}</td><td>{{ l.counted ? '是' : '否' }}</td>
                        </tr>
                        <tr v-if="!detail.logs.length"><td colspan="5">无识别日志</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const alerts = ref([])
const sessions = ref([])
const expanded = ref(null)
const detail = ref(null)

function fmt(t) { return t ? t.replace('T', ' ').slice(0, 19) : '-' }

async function load() {
  const [a, s] = await Promise.all([api.get('/alerts'), api.get('/sessions')])
  alerts.value = a.data
  sessions.value = s.data
}

async function resolve(a) {
  await api.post(`/alerts/${a.id}/resolve`)
  await load()
}

async function toggle(s) {
  if (expanded.value === s.id) { expanded.value = null; return }
  const { data } = await api.get(`/sessions/${s.id}`)
  detail.value = data
  expanded.value = s.id
}

onMounted(load)
</script>
