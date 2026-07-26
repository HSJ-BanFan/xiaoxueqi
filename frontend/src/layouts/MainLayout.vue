<template>
  <div class="main-layout">
    <el-container>
      <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
        <div class="logo">
          <h2 v-if="!isCollapse">糖尿病助理</h2>
          <h2 v-else>糖</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :router="true"
          :collapse="isCollapse"
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
          
          <el-menu-item index="/devices">
            <el-icon><Monitor /></el-icon>
            <template #title>设备管理</template>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>设置</template>
          </el-menu-item>
        </el-menu>
        
        <div class="sidebar-footer">
          <el-button type="text" @click="isCollapse = !isCollapse" class="collapse-btn">
            <el-icon v-if="isCollapse"><Expand /></el-icon>
            <el-icon v-else><Fold /></el-icon>
          </el-button>
          
          <el-button type="danger" @click="confirmLogout" class="logout-btn">
            <el-icon><SwitchButton /></el-icon>
            <span v-if="!isCollapse">退出登录</span>
          </el-button>
        </div>
      </el-aside>
      
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-dropdown trigger="click" @command="handleCommand">
              <div class="user-info">
                <el-avatar :size="32" :src="userAvatar">{{ userInitial }}</el-avatar>
                <span class="username">{{ userName }}</span>
                <el-icon><CaretBottom /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
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
          <router-view v-slot="{ Component }">
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { 
  Grid, 
  DataAnalysis, 
  Bowl, 
  Aim, 
  ChatLineRound, 
  Reading, 
  Setting,
  Expand,
  Fold,
  CaretBottom,
  SwitchButton,
  User,
  Monitor
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)

const userAvatar = computed(() => userStore.user.avatar || '')
const userName = computed(() => userStore.user.name || '用户')
const userInitial = computed(() => {
  return userName.value.charAt(0).toUpperCase()
})

const pageMap = {
  '/dashboard': '仪表盘',
  '/glucose': '血糖记录',
  '/diet': '饮食管理',
  '/health': '健康数据',
  '/assistant': '智能助理',
  '/knowledge': '知识库',
  '/devices': '设备管理',
  '/settings': '设置',
  '/profile': '个人信息'
}

const currentPageTitle = computed(() => {
  return pageMap[route.path] || '页面'
})

const handleCommand = (command: string) => {
  if (command === 'profile') {
    router.push({ path: '/settings', hash: '#health-profile' })
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
    }).catch(() => {})
  }
}

const confirmLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
  }).catch(() => {})
}

// 监听窗口大小变化，在小屏幕上自动折叠侧边栏
const handleResize = () => {
  isCollapse.value = window.innerWidth < 768
}

watch(
  () => route.path,
  () => {
    if (window.innerWidth < 768) {
      isCollapse.value = true
    }
  }
)

// 组件挂载时添加窗口大小变化监听
onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时移除窗口大小变化监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background-color: #304156;
  color: white;
  height: 100vh;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  color: white;
  margin: 0;
  font-size: 1.2rem;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background-color: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  color: #bfcbd9;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #409eff;
  background-color: #263445;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: #263445;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
}

.collapse-btn {
  color: #bfcbd9;
}

.logout-btn {
  width: 100%;
  justify-content: center;
  background-color: #f56c6c;
  color: white;
  border: none;
}

.logout-btn:hover {
  background-color: #f78989;
}

.logout-btn :deep(.el-icon) {
  margin-right: 5px;
}

.header {
  background-color: white;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px !important;
  }
  
  .username {
    display: none;
  }
}
</style>
