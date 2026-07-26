<template>
  <div class="main-layout">
    <el-container class="layout-shell">
      <el-aside :width="isCollapse ? '72px' : '220px'" class="sidebar">
        <button class="logo" type="button" @click="goHome" :title="isCollapse ? '糖尿病助理' : undefined">
          <span class="logo-mark">糖</span>
          <span v-if="!isCollapse" class="logo-text">糖尿病助理</span>
        </button>

        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :router="true"
          :collapse="isCollapse"
          :collapse-transition="false"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Grid /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <el-menu-item index="/glucose">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>血糖记录</template>
          </el-menu-item>

          <el-menu-item index="/diet">
            <el-icon><Bowl /></el-icon>
            <template #title>饮食管理</template>
          </el-menu-item>

          <el-menu-item index="/health">
            <el-icon><Aim /></el-icon>
            <template #title>健康数据</template>
          </el-menu-item>

          <el-menu-item index="/assistant">
            <el-icon><ChatLineRound /></el-icon>
            <template #title>智能助理</template>
          </el-menu-item>

          <el-menu-item index="/knowledge">
            <el-icon><Reading /></el-icon>
            <template #title>知识库</template>
          </el-menu-item>

          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>设置</template>
          </el-menu-item>
        </el-menu>

        <div class="sidebar-footer">
          <el-button text class="collapse-btn" @click="isCollapse = !isCollapse">
            <el-icon v-if="isCollapse"><Expand /></el-icon>
            <el-icon v-else><Fold /></el-icon>
            <span v-if="!isCollapse">收起侧栏</span>
          </el-button>
        </div>
      </el-aside>

      <el-container class="content-shell">
        <el-header class="header" height="56px">
          <div class="header-left">
            <el-button
              class="home-btn"
              text
              type="primary"
              @click="goHome"
            >
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-button>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">仪表盘</el-breadcrumb-item>
              <el-breadcrumb-item v-if="route.path !== '/dashboard'">
                {{ currentPageTitle }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <el-button
              v-if="route.path !== '/assistant'"
              type="primary"
              plain
              size="small"
              round
              @click="router.push('/assistant')"
            >
              智能助理
            </el-button>

            <el-dropdown trigger="click" @command="handleCommand">
              <div class="user-info">
                <el-avatar :size="32" :src="userAvatar || undefined">{{ userInitial }}</el-avatar>
                <span class="username">{{ userName }}</span>
                <el-icon><CaretBottom /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="home">
                    <el-icon><HomeFilled /></el-icon>
                    返回仪表盘
                  </el-dropdown-item>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="logout" divided>
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view v-slot="{ Component, route: viewRoute }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="viewRoute.path" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  Aim,
  Bowl,
  CaretBottom,
  ChatLineRound,
  DataAnalysis,
  Expand,
  Fold,
  Grid,
  HomeFilled,
  Reading,
  Setting,
  SwitchButton,
  User
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenu = computed(() => {
  if (route.path.startsWith('/glucose')) return '/glucose'
  return route.path
})

const userAvatar = computed(() => userStore.user?.avatar || '')
const userName = computed(() => userStore.user?.name || userStore.userFullName || '用户')
const userInitial = computed(() => userName.value.charAt(0).toUpperCase() || 'U')

const pageMap: Record<string, string> = {
  '/dashboard': '仪表盘',
  '/glucose': '血糖记录',
  '/glucose-record': '记录血糖',
  '/diet': '饮食管理',
  '/health': '健康数据',
  '/assistant': '智能助理',
  '/knowledge': '知识库',
  '/settings': '设置'
}

const currentPageTitle = computed(() => {
  const metaTitle = route.meta.title
  if (typeof metaTitle === 'string' && metaTitle) return metaTitle
  return pageMap[route.path] || '页面'
})

const goHome = () => {
  if (route.path !== '/dashboard') {
    router.push('/dashboard')
  }
}

const handleCommand = (command: string) => {
  if (command === 'home') {
    goHome()
    return
  }

  if (command === 'profile') {
    router.push({ path: '/settings', hash: '#health-profile' })
    return
  }

  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(() => {
        userStore.logout()
      })
      .catch(() => {})
  }
}

const handleResize = () => {
  isCollapse.value = window.innerWidth < 1100
}

watch(
  () => route.path,
  () => {
    if (window.innerWidth < 1100) {
      isCollapse.value = true
    }
  }
)

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout,
.layout-shell {
  height: 100vh;
  overflow: hidden;
  background: #eef2f7;
}

.sidebar {
  display: flex;
  flex-direction: column;
  height: 100vh;
  color: #fff;
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  transition: width 0.2s ease;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 56px;
  padding: 0 16px;
  border: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent;
  color: #fff;
  cursor: pointer;
}

.logo:hover {
  background: rgba(255, 255, 255, 0.04);
}

.logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  font-size: 15px;
  font-weight: 700;
}

.logo-text {
  font-size: 15px;
  font-weight: 650;
  letter-spacing: 0.02em;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
  padding: 10px 8px;
  overflow-y: auto;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 100%;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 4px;
  border-radius: 10px;
  color: #cbd5e1;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: rgba(99, 102, 241, 0.28);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06);
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.collapse-btn {
  width: 100%;
  justify-content: flex-start;
  color: #cbd5e1;
  gap: 8px;
}

.content-shell {
  min-width: 0;
  height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid #e5eaf0;
  backdrop-filter: blur(8px);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.home-btn {
  padding: 4px 8px;
  font-weight: 600;
}

.home-btn .el-icon {
  margin-right: 4px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 220px;
  cursor: pointer;
}

.username {
  overflow: hidden;
  color: #1f2a37;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-content {
  height: calc(100vh - 56px);
  padding: 12px 14px 18px;
  overflow: auto;
  background:
    radial-gradient(circle at top left, rgba(99, 102, 241, 0.05), transparent 28%),
    #eef2f7;
}

.main-content > * {
  width: 100%;
  max-width: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .username {
    display: none;
  }

  .main-content {
    padding: 10px 10px 16px;
  }

  .header {
    padding: 0 10px;
  }
}
</style>
