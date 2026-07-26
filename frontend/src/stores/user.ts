import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import axios from 'axios'
import router from '../router'
import { ElMessage } from 'element-plus'
import { apiClient, userApi } from '../api'
import type { User, UserCreate, UserUpdate } from '../types/models'

type StoredUser = Partial<User>

const readStoredUser = (): StoredUser => {
  const raw = localStorage.getItem('user')
  if (!raw) return {}

  try {
    return JSON.parse(raw) as StoredUser
  } catch {
    localStorage.removeItem('user')
    return {}
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<StoredUser>(readStoredUser())
  const useLocalAuth = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value && user.value.id))
  const userFullName = computed(
    () => user.value.name || user.value.full_name || user.value.email?.split('@')[0] || '用户'
  )

  const persistUser = (profile: StoredUser) => {
    user.value = profile
    localStorage.setItem('user', JSON.stringify(profile))
  }

  /**
   * 读取服务端完整 profile。登录响应只保证 id/email，因此页面进入时必须走这里。
   */
  async function fetchProfile(): Promise<User | null> {
    if (!token.value) return null

    const response = await userApi.getProfile()
    const profile = response.data
    if (!profile?.id) {
      throw new Error('用户资料响应缺少 id')
    }

    persistUser(profile)
    return profile
  }

  // 保留旧调用名，所有调用都走完整 profile 请求。
  const fetchUserProfile = fetchProfile
  const getUserInfo = fetchProfile

  async function login(email: string, password: string) {
    try {
      if (
        useLocalAuth.value &&
        ((email === 'admin@example.com' && password === 'admin') ||
          (email === 'test@example.com' && password === 'test123'))
      ) {
        const mockToken = `mock_token_${Date.now()}`
        token.value = mockToken
        localStorage.setItem('token', mockToken)

        const mockUser: StoredUser =
          email === 'admin@example.com'
            ? {
                id: 'admin-id',
                email,
                name: '系统管理员',
                is_active: true,
                is_superuser: true
              }
            : {
                id: 'test-id',
                email,
                name: '测试用户',
                is_active: true,
                is_superuser: false
              }

        persistUser(mockUser)
        ElMessage.success('登录成功')
        await router.push((router.currentRoute.value.query.redirect as string) || '/dashboard')
        return true
      }

      const response = await userApi.login(email, password)
      const data = response.data as { access_token?: string; user_id?: string; id?: string; email?: string; name?: string }
      const userId = data.user_id || data.id
      if (!data.access_token || !userId) {
        throw new Error('登录响应缺少必要信息')
      }

      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user_id', userId)
      localStorage.setItem('email', data.email || email)

      // 先写入最小对象，避免守卫在 profile 请求期间丢失登录态。
      persistUser({
        id: userId,
        email: data.email || email,
        name: data.name || `用户${email.split('@')[0]}`,
        is_active: true
      })

      // profile 失败时仍保留可用的最小登录态；Settings/Dashboard 会再次重试。
      try {
        await fetchProfile()
      } catch {
        // 网络暂时不可用不应抹掉刚刚建立的登录态。
      }

      ElMessage.success('登录成功')
      await router.push((router.currentRoute.value.query.redirect as string) || '/dashboard')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || error.message || '登录失败：用户名或密码错误')
      return false
    }
  }

  async function register(userData: UserCreate | Record<string, unknown>) {
    await userApi.register(userData)
    ElMessage.success('注册成功，请登录')
    await router.push('/login')
    return true
  }

  function logout() {
    token.value = ''
    user.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('user_id')
    localStorage.removeItem('email')
    void router.push('/login')
    ElMessage.success('已退出登录')
  }

  async function updateProfile(userData: UserUpdate): Promise<User> {
    if (useLocalAuth.value) {
      const safeProfileUpdates = { ...userData }
      delete safeProfileUpdates.password
      const nextUser = { ...user.value, ...safeProfileUpdates } as User
      persistUser(nextUser)
      return nextUser
    }

    const response = await userApi.updateProfile(userData)
    const profile = response.data
    persistUser(profile)
    return profile
  }

  function toggleAuthMode(useLocal: boolean) {
    useLocalAuth.value = useLocal
    return useLocalAuth.value
  }

  function initialize() {
    // 无论 localStorage 中是否有残缺对象，只要存在 token 就刷新一次完整 profile。
    if (token.value) {
      void fetchProfile().catch(() => undefined)
    }
  }

  // 兼容少量仍直接使用 axios 的旧页面，同时保持统一鉴权头。
  axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
  axios.interceptors.request.use(config => {
    if (token.value) {
      config.headers.Authorization = `Bearer ${token.value}`
    }
    return config
  })

  apiClient.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        logout()
      }
      return Promise.reject(error)
    }
  )

  initialize()

  return {
    token,
    user,
    isAuthenticated,
    userFullName,
    useLocalAuth,
    login,
    register,
    fetchProfile,
    fetchUserProfile,
    getUserInfo,
    logout,
    updateProfile,
    toggleAuthMode,
    initialize
  }
})
