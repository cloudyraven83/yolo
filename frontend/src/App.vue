<template>
  <div>
    <nav class="topnav">
      <span class="brand" @click="$router.push('/')"><span class="brand-dot"></span>无人饮料售货机</span>
      <div class="links">
        <router-link to="/">顾客操作台</router-link>
        <template v-if="username">
          <router-link to="/admin">运营概览</router-link>
          <router-link to="/admin/inventory">库存补货</router-link>
          <router-link to="/admin/records">预警与记录</router-link>
        </template>
      </div>
      <div class="right">
        <span v-if="username" class="user">{{ username }}</span>
        <a v-if="username" href="#" @click.prevent="logout">退出</a>
        <router-link v-else to="/admin/login">管理员登录</router-link>
      </div>
    </nav>
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const username = ref(localStorage.getItem('username'))
watch(() => route.fullPath, () => { username.value = localStorage.getItem('username') })

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  username.value = null
  router.push('/')
}
</script>
