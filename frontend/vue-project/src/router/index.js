import { createRouter, createWebHistory } from 'vue-router'
import { storage } from '../utils/storage'
import { authApi } from '../api/auth'
import SettingsView from '@/views/settings/SettingsView.vue'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/auth'
  },
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('../views/auth/AuthView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/chat/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: () => import('../views/user/UserCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = storage.getToken()
  
  // 如果是登录页面，直接通过
  if (to.name === 'Auth') {
    if (token) {
      next('/chat')
    } else {
      next()
    }
    return
  }
  
  // 需要认证的页面才检查token
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/auth')
      return
    }
    
    // 验证token有效性
    try {
      const res = await authApi.checkLoginStatus()
      if (!res.success) {
        storage.clearAuth()
        next('/auth')
        return
      }
    } catch (error) {
      storage.clearAuth()
      next('/auth')
      return
    }
  }
  
  next()
})

export default router 