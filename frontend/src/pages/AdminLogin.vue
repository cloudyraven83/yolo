<template>
  <div class="login-wrap">
    <div class="panel login-card">
      <h2>管理员登录</h2>
      <input v-model="username" placeholder="用户名" @keyup.enter="login" />
      <input v-model="password" type="password" placeholder="密码" @keyup.enter="login" />
      <button class="btn primary full" @click="login">登录</button>
      <p v-if="err" class="msg">{{ err }}</p>
      <p class="hint">初始账号：admin / admin123</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const username = ref('')
const password = ref('')
const err = ref('')
const router = useRouter()

async function login() {
  err.value = ''
  try {
    const { data } = await api.post('/admin/login', {
      username: username.value, password: password.value,
    })
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.username)
    router.push('/admin')
  } catch (e) {
    err.value = e.response?.data?.detail || '登录失败'
  }
}
</script>
