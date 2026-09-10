<template>
  <div>
    <div class="page-head">
      <h2>库存补货</h2>
      <p class="sub">货道库存与补货管理，库存低于阈值自动预警</p>
    </div>
    <div class="panel">
    <h3>货道库存 <small>（库存低于阈值自动预警）</small></h3>
    <div class="table-wrap">
    <table class="table">
      <thead>
        <tr><th>货道</th><th>商品</th><th>品牌</th><th>单价</th><th>库存/容量</th><th>阈值</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="x in rows" :key="x.lane_id">
          <td>{{ x.shelf_no }}</td>
          <td>{{ x.name }}</td>
          <td>{{ x.brand }}</td>
          <td>¥{{ x.price.toFixed(2) }}</td>
          <td>{{ x.stock }} / {{ x.capacity }}</td>
          <td>{{ x.threshold }}</td>
          <td><span class="badge" :class="x.low_stock ? 'open' : 'idle'">{{ x.low_stock ? '需补货' : '正常' }}</span></td>
          <td>
            <button class="btn small primary" @click="openRestock(x)">补货</button>
            <button class="btn small" @click="openEdit(x)">编辑</button>
          </td>
        </tr>
      </tbody>
    </table>
    </div>
    </div>

    <div v-if="modal" class="modal-mask" @click.self="modal = null">
      <div class="panel modal">
        <h3>{{ modal.type === 'restock' ? '补货登记' : '编辑货道' }} — {{ modal.row.shelf_no }} {{ modal.row.name }}</h3>
        <template v-if="modal.type === 'restock'">
          <label>补货数量</label>
          <input type="number" v-model.number="modal.qty" min="1" />
        </template>
        <template v-else>
          <label>单价（元）</label>
          <input type="number" v-model.number="modal.price" step="0.1" min="0" />
          <label>补货阈值</label>
          <input type="number" v-model.number="modal.threshold" min="0" />
          <label>货道容量</label>
          <input type="number" v-model.number="modal.capacity" min="0" />
        </template>
        <div class="btn-row">
          <button class="btn primary" @click="submit">确认</button>
          <button class="btn" @click="modal = null">取消</button>
        </div>
        <p v-if="modal.err" class="msg">{{ modal.err }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const rows = ref([])
const modal = ref(null)

async function load() {
  const { data } = await api.get('/inventory')
  rows.value = data
}

function openRestock(x) {
  modal.value = { type: 'restock', row: x, qty: 5, err: '' }
}

function openEdit(x) {
  modal.value = { type: 'edit', row: x, price: x.price, threshold: x.threshold, capacity: x.capacity, err: '' }
}

async function submit() {
  const m = modal.value
  try {
    if (m.type === 'restock') {
      await api.post('/restock', { lane_id: m.row.lane_id, quantity: m.qty })
    } else {
      await api.put(`/inventory/lane/${m.row.lane_id}`, {
        price: m.price, threshold: m.threshold, capacity: m.capacity,
      })
    }
    modal.value = null
    await load()
  } catch (e) {
    m.err = e.response?.data?.detail || '操作失败'
  }
}

onMounted(load)
</script>
