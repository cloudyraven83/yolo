import { createRouter, createWebHistory } from 'vue-router'
import CashierView from '../pages/CashierView.vue'
import AdminLogin from '../pages/AdminLogin.vue'
import Dashboard from '../pages/Dashboard.vue'
import Inventory from '../pages/Inventory.vue'
import AlertsRecords from '../pages/AlertsRecords.vue'

const routes = [
  { path: '/', component: CashierView },
  { path: '/admin/login', component: AdminLogin },
  { path: '/admin', component: Dashboard, meta: { auth: true } },
  { path: '/admin/inventory', component: Inventory, meta: { auth: true } },
  { path: '/admin/records', component: AlertsRecords, meta: { auth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.auth && !localStorage.getItem('token')) return '/admin/login'
})

export default router
