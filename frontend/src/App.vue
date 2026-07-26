<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <router-view />
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}
</style>
