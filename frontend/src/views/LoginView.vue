<template>
  <div class="login-container">
    <div class="background-animation"></div>
    <div class="login-card glass-effect">
      <div class="login-header">
        <h2>糖尿病智能健康助理</h2>
        <p>欢迎回来，请登录</p>
      </div>

      <el-form
        ref="loginForm"
        :model="loginData"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="loginData.email"
            placeholder="邮箱"
            type="email"
            prefix-icon="el-icon-message"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginData.password"
            placeholder="密码"
            type="password"
            prefix-icon="el-icon-lock"
            show-password
            size="large"
          />
        </el-form-item>

        <div class="login-options">
          <el-checkbox v-model="loginData.remember">记住我</el-checkbox>
          <a href="#" class="forgot-password-link">忘记密码?</a>
        </div>

        <el-button
          type="primary"
          native-type="submit"
          :loading="loading"
          class="login-button"
          size="large"
        >
          {{ loading ? '登录中...' : '登 录' }}
        </el-button>

        <div class="register-link">
          还没有账号? <router-link to="/register">立即注册</router-link>
        </div>

      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const loading = ref(false)

const loginData = reactive({
  email: '',
  password: '',
  remember: false
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, message: '密码长度不能少于4个字符', trigger: 'blur' }
  ]
}

const loginForm = ref()

onMounted(() => {
  // 如果用户已登录，直接跳转到首页或重定向页面
  if (userStore.isAuthenticated) {
    const redirectPath = route.query.redirect as string
    router.push(redirectPath || '/dashboard')
  }
})

const handleLogin = async () => {
  if (!loginForm.value) return
  
  await loginForm.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        const success = await userStore.login(loginData.email, loginData.password)
        if (!success) {
          ElMessage.error('登录失败，请检查您的邮箱和密码')
        }
      } catch {
        ElMessage.error('登录失败，请检查您的邮箱和密码')
      } finally {
        loading.value = false
      }
    } else {
      ElMessage.warning('请填写正确的登录信息')
      return false
    }
  })
}

</script>

<style scoped>
@keyframes gradient-animation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.background-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(-45deg, #0d1117, #1a202c, #4f46e5, #c026d3);
  background-size: 400% 400%;
  animation: gradient-animation 10s ease infinite;
  z-index: 0;
}

.login-card.glass-effect {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 40px;
  background: rgba(22, 27, 34, 0.7);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  color: #e6edf3;
  animation: fadeInUp 0.8s 0.3s ease-in-out forwards;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.login-header p {
  color: #c9d1d9;
  font-size: 14px;
}

.login-form .el-form-item {
  margin-bottom: 25px;
}

:deep(.el-input__wrapper) {
  background-color: rgba(33, 41, 54, 0.7) !important;
  border: 1px solid #30363d !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: #e6edf3 !important;
}

:deep(.el-input__inner:-webkit-autofill) {
  -webkit-box-shadow: 0 0 0 1000px rgba(33, 41, 54, 0.9) inset !important;
  -webkit-text-fill-color: #e6edf3 !important;
}

:deep(.el-input__prefix .el-icon) {
  color: #8b949e;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 14px;
}

:deep(.el-checkbox__label) {
  color: #c9d1d9;
}

.forgot-password-link {
  color: #58a6ff;
  text-decoration: none;
  transition: color 0.3s;
}
.forgot-password-link:hover {
  color: #388bfd;
  text-decoration: underline;
}

.login-button {
  width: 100%;
  font-weight: 600;
  border: none;
  background: linear-gradient(to right, #58a6ff, #388bfd);
  transition: all 0.3s ease;
  letter-spacing: 1px;
}
.login-button:hover {
  opacity: 0.9;
  box-shadow: 0 0 15px rgba(56, 139, 253, 0.5);
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #8b949e;
}
.register-link a {
  color: #58a6ff;
  text-decoration: none;
  font-weight: 600;
}
.register-link a:hover {
  text-decoration: underline;
}

</style>
