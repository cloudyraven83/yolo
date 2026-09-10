<template>
  <div class="cashier">
    <div class="panel video-panel">
      <div class="video-head">
        <span class="badge" :class="[state, { pulse: state === 'open' }]">{{ stateText }}</span>
        <span class="provider">识别通道：{{ providerText }}
          <a href="#" @click.prevent="switchProvider(provider === 'simulated' ? 'yolo' : 'simulated')">切换</a>
        </span>
      </div>
      <div class="video-wrap">
        <img class="video" :src="streamUrl" alt="摄像头预览" />
      </div>
      <p class="hint">请将饮料对准摄像头；开门后开始识别，关门自动结算。</p>
    </div>

    <div class="panel ctrl-panel">
      <div v-if="!settlement">
        <h3>售货操作</h3>
        <div class="btn-row">
          <button class="btn primary" :disabled="state === 'open'" @click="start">开门 · 开始识别</button>
          <button class="btn danger" :disabled="state !== 'open'" @click="stop">关门 · 结束识别</button>
        </div>

        <h3>演示场景注入 <small>（模拟拿走饮料）</small></h3>
        <div class="scenario-form">
          <select v-model.number="selProduct">
            <option v-for="p in products" :key="p.id" :value="p.id">
              {{ p.name }}（¥{{ p.price.toFixed(2) }}）
            </option>
          </select>
          <input type="number" v-model.number="selQty" min="1" max="20" />
          <button class="btn" @click="addItem">加入</button>
        </div>
        <ul class="scenario-list">
          <li v-for="(it, i) in scenario" :key="i">
            {{ it.name }} × {{ it.qty }}
            <a href="#" @click.prevent="scenario.splice(i, 1)">移除</a>
          </li>
          <li v-if="!scenario.length" class="empty">尚未添加演示商品</li>
        </ul>
        <button class="btn warn" :disabled="state !== 'open' || !scenario.length" @click="inject">
          注入场景（模拟拿走）
        </button>
        <p v-if="msg" class="msg">{{ msg }}</p>
      </div>

      <div v-else class="settlement">
        <h3>结算单 <small>#{{ settlement.session_id }}</small></h3>
        <table class="table">
          <thead><tr><th>商品</th><th>数量</th><th>单价</th><th>小计</th></tr></thead>
          <tbody>
            <tr v-for="it in settlement.items" :key="it.product_id">
              <td>{{ it.name }}</td><td>{{ it.quantity }}</td>
              <td>¥{{ it.unit_price.toFixed(2) }}</td><td>¥{{ it.subtotal.toFixed(2) }}</td>
            </tr>
            <tr v-if="!settlement.items.length"><td colspan="4">本次未拿走商品</td></tr>
          </tbody>
        </table>
        <div class="total">应付合计：<b>¥{{ settlement.total_amount.toFixed(2) }}</b></div>
        <p v-for="w in settlement.warnings" :key="w" class="warn-text">{{ w }}</p>
        <div class="btn-row">
          <button v-if="!paid" class="btn primary" @click="pay">模拟支付</button>
          <button v-else class="btn" @click="resetAll">开始新一轮</button>
        </div>
        <p v-if="paid" class="msg ok">支付成功（模拟），感谢惠顾！</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'

const state = ref('idle')
const provider = ref('simulated')
const streamUrl = '/api/camera/stream'
const products = ref([])
const scenario = ref([])
const selProduct = ref(null)
const selQty = ref(1)
const settlement = ref(null)
const paid = ref(false)
const msg = ref('')
let timer = null

const stateText = computed(() => ({ idle: '待机', open: '识别中（门已开）', closed: '待支付' }[state.value] || state.value))
const providerText = computed(() => provider.value === 'simulated' ? '模拟识别' : 'YOLO 摄像头')

async function refresh() {
  try {
    const { data } = await api.get('/session/current')
    state.value = data.state
    provider.value = data.provider
  } catch (e) { /* 忽略轮询异常 */ }
}

async function start() {
  msg.value = ''
  try { await api.post('/session/start'); await refresh() }
  catch (e) { msg.value = e.response?.data?.detail || '开门失败' }
}

async function stop() {
  msg.value = ''
  try {
    const { data } = await api.post('/session/stop')
    settlement.value = data
    paid.value = false
    await refresh()
  } catch (e) { msg.value = e.response?.data?.detail || '关门失败' }
}

async function pay() {
  try {
    await api.post(`/session/${settlement.value.session_id}/pay`)
    paid.value = true
    await refresh()
  } catch (e) { msg.value = e.response?.data?.detail || '支付失败' }
}

function resetAll() {
  settlement.value = null
  paid.value = false
  refresh()
}

function addItem() {
  const p = products.value.find((x) => x.id === selProduct.value)
  if (!p || selQty.value < 1) return
  scenario.value.push({ product_id: p.id, name: p.name, qty: selQty.value })
}

async function inject() {
  msg.value = ''
  try {
    const { data } = await api.post('/demo/scenario', {
      items: scenario.value.map((i) => ({ product_id: i.product_id, qty: i.qty })),
    })
    msg.value = `已注入 ${data.injected_events} 件拿走事件，请关门结算`
    scenario.value = []
  } catch (e) { msg.value = e.response?.data?.detail || '注入失败' }
}

async function switchProvider(name) {
  msg.value = ''
  try {
    const { data } = await api.post('/model/switch', { provider: name })
    provider.value = data.current
    if (data.provider && data.provider.available === false) {
      msg.value = data.provider.error || '该通道不可用（未安装依赖或未接入摄像头）'
    }
  } catch (e) { msg.value = e.response?.data?.detail || '切换失败' }
}

onMounted(async () => {
  const { data } = await api.get('/products')
  products.value = data
  selProduct.value = data[0]?.id ?? null
  await refresh()
  timer = setInterval(refresh, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>
