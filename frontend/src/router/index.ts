import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const LoginView = () => import('../views/LoginView.vue')
const RegisterView = () => import('../views/RegisterView.vue')
const MainLayout = () => import('../layouts/MainLayout.vue')
const DashboardView = () => import('../views/DashboardView.vue')
const HealthView = () => import('../views/HealthView.vue')
const GlucoseView = () => import('../views/GlucoseView.vue')
const DietView = () => import('../views/DietView.vue')
const AssistantView = () => import('../views/AssistantView.vue')
const KnowledgeView = () => import('../views/KnowledgeView.vue')
const SettingsView = () => import('../views/SettingsView.vue')
const NotFoundView = () => import('../views/NotFoundView.vue')
const GlucoseRecordView = () => import('../views/GlucoseRecordView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard'
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: { requiresAuth: true, title: '仪表盘' }
        },
        {
          path: 'health',
          name: 'health',
          component: HealthView,
          meta: { requiresAuth: true, title: '健康数据' }
        },
        {
          path: 'glucose',
          name: 'glucose',
          component: GlucoseView,
          meta: { requiresAuth: true, title: '血糖记录' }
        },
        {
          path: 'glucose-record',
          name: 'glucose-record',
          component: GlucoseRecordView,
          meta: { requiresAuth: true, title: '记录血糖' }
        },
        {
          path: 'diet',
          name: 'diet',
          component: DietView,
          meta: { requiresAuth: true, title: '饮食管理' }
        },
        {
          path: 'assistant',
          name: 'assistant',
          component: AssistantView,
          meta: { requiresAuth: true, title: '智能助理' }
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: KnowledgeView,
          meta: { requiresAuth: true, title: '知识库' }
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsView,
          meta: { requiresAuth: true, title: '设置' }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: { requiresAuth: false }
    }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth === true)

  if (!requiresAuth) {
    next()
    return
  }

  if (!userStore.isAuthenticated) {
    next({
      name: 'login',
      query: { redirect: to.fullPath },
      replace: true
    })
    return
  }

  next()
})

export default router
