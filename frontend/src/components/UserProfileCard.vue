<template>
  <el-card class="user-profile-card" shadow="never">
    <template #header>
      <div class="card-header">
        <div>
          <span>我的健康档案</span>
          <small>身份、目标与近 7 天概况</small>
        </div>
        <el-button text type="primary" @click="goToSettings">编辑</el-button>
      </div>
    </template>

    <el-skeleton v-if="profileLoading && !displayProfile.id" :rows="6" animated />

    <div v-else class="profile-content">
      <el-alert
        v-if="profileError"
        class="inline-alert"
        title="完整档案暂时无法加载"
        type="warning"
        :closable="false"
        show-icon
      />

      <div class="identity-row">
        <el-avatar :size="58" :src="displayProfile.avatar || undefined">
          {{ userInitial }}
        </el-avatar>
        <div class="identity-copy">
          <strong>{{ displayName }}</strong>
          <span>{{ displayProfile.email || '邮箱未设置' }}</span>
        </div>
        <el-tag :type="profileIncomplete ? 'warning' : 'success'" effect="light" size="small">
          {{ profileIncomplete ? '档案待完善' : '档案已完善' }}
        </el-tag>
      </div>

      <div class="profile-grid">
        <div class="profile-item">
          <span>糖尿病类型</span>
          <strong>{{ diabetesTypeLabel }}</strong>
        </div>
        <div class="profile-item">
          <span>目标血糖</span>
          <strong>{{ targetRangeText }}</strong>
        </div>
        <div class="profile-item">
          <span>身高</span>
          <strong>{{ heightText }}</strong>
        </div>
        <div class="profile-item">
          <span>体重</span>
          <strong>{{ weightText }}</strong>
        </div>
        <div class="profile-item">
          <span>BMI</span>
          <strong>{{ bmiText }}</strong>
        </div>
      </div>

      <div v-if="profileIncomplete" class="profile-guidance">
        <span>完善档案后助理与图表更准</span>
        <el-button type="primary" link @click="goToSettings">去完善</el-button>
      </div>

      <el-divider />

      <div class="weekly-heading">
        <div>
          <strong>近 7 天血糖</strong>
          <span>按当前目标区间统计</span>
        </div>
        <el-button v-if="statsError" link type="primary" @click="loadWeeklyStats">重试</el-button>
      </div>

      <el-skeleton v-if="statsLoading" :rows="2" animated />

      <el-alert
        v-else-if="statsError"
        class="inline-alert"
        title="近 7 天统计暂时不可用"
        type="info"
        :closable="false"
        show-icon
      />

      <el-empty v-else-if="!hasWeeklyData" class="compact-empty" description="近 7 天还没有血糖记录" :image-size="64">
        <el-button type="primary" size="small" @click="goToGlucoseRecord">去记录血糖</el-button>
      </el-empty>

      <div v-else>
        <div class="weekly-grid">
          <div class="weekly-stat">
            <strong>{{ weeklyAverage }}</strong>
            <span>均值 mmol/L</span>
          </div>
          <div class="weekly-stat">
            <strong>{{ weeklyStats?.count }}</strong>
            <span>记录条数</span>
          </div>
          <div class="weekly-stat">
            <strong>{{ inRangePercentage }}%</strong>
            <span>达标率</span>
          </div>
        </div>
        <el-tag :type="weeklyStatus.type" effect="plain" class="weekly-status">
          {{ weeklyStatus.label }}
        </el-tag>
      </div>

      <div class="card-actions">
        <el-button type="primary" @click="goToGlucoseRecord">记录血糖</el-button>
        <el-button @click="goToAssistant">问助理解读</el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { glucoseApi } from '../api'
import { useUserStore } from '../stores/user'
import type { DiabetesType, GlucoseStatistics, User } from '../types/models'

type TagType = 'success' | 'warning' | 'danger' | 'info'

const props = defineProps<{
  profile?: User | null
}>()

const router = useRouter()
const userStore = useUserStore()

const profileLoading = ref(true)
const profileError = ref(false)
const statsLoading = ref(true)
const statsError = ref(false)
const weeklyStats = ref<GlucoseStatistics | null>(null)

const diabetesTypeLabels: Record<DiabetesType, string> = {
  type1: '1 型糖尿病',
  type2: '2 型糖尿病',
  gestational: '妊娠期糖尿病',
  prediabetes: '糖尿病前期',
  other: '其他'
}

const displayProfile = computed<Partial<User>>(() => props.profile || userStore.user)
const displayName = computed(
  () => displayProfile.value.name || displayProfile.value.full_name || '用户'
)
const userInitial = computed(() => displayName.value.trim().charAt(0).toUpperCase() || '用')

const diabetesTypeLabel = computed(() => {
  const type = displayProfile.value.diabetes_type
  return type ? diabetesTypeLabels[type] : '未设置'
})

const targetRangeText = computed(() => {
  const min = displayProfile.value.target_glucose_min
  const max = displayProfile.value.target_glucose_max
  if (typeof min !== 'number' || typeof max !== 'number') return '未设置'
  return `${min.toFixed(1)}–${max.toFixed(1)} mmol/L`
})

const heightText = computed(() => {
  const height = displayProfile.value.height
  return typeof height === 'number' ? `${height.toFixed(1)} cm` : '未设置'
})

const weightText = computed(() => {
  const weight = displayProfile.value.weight
  return typeof weight === 'number' ? `${weight.toFixed(1)} kg` : '未设置'
})

const bmiText = computed(() => {
  const height = displayProfile.value.height
  const weight = displayProfile.value.weight
  if (typeof height !== 'number' || typeof weight !== 'number' || height <= 0) return '未设置'
  return (weight / Math.pow(height / 100, 2)).toFixed(1)
})

const profileIncomplete = computed(
  () =>
    !displayProfile.value.diabetes_type ||
    typeof displayProfile.value.target_glucose_min !== 'number' ||
    typeof displayProfile.value.target_glucose_max !== 'number'
)

const hasWeeklyData = computed(() => Boolean(weeklyStats.value && weeklyStats.value.count > 0))
const weeklyAverage = computed(() => (weeklyStats.value?.average ?? 0).toFixed(1))
const inRangePercentage = computed(() => Math.round(weeklyStats.value?.in_range_percentage ?? 0))

const weeklyStatus = computed<{ label: string; type: TagType }>(() => {
  const stats = weeklyStats.value
  if (!stats || stats.count === 0) return { label: '暂无数据', type: 'info' }
  if (stats.in_range_percentage >= 70) return { label: '多数记录处于目标范围', type: 'success' }
  if (stats.high_percentage > stats.low_percentage) {
    return { label: '偏高记录占比较多，请持续观察', type: 'warning' }
  }
  if (stats.low_percentage > 0) {
    return { label: '存在偏低记录，请持续观察', type: 'danger' }
  }
  return { label: '记录分布仍需继续观察', type: 'info' }
})

const loadProfile = async () => {
  profileLoading.value = true
  profileError.value = false
  try {
    if (!props.profile && userStore.token) {
      await userStore.fetchProfile()
    }
  } catch {
    profileError.value = true
  } finally {
    profileLoading.value = false
  }
}

const loadWeeklyStats = async () => {
  statsLoading.value = true
  statsError.value = false
  try {
    const response = await glucoseApi.getStatistics('week')
    weeklyStats.value = response.data
  } catch {
    weeklyStats.value = null
    statsError.value = true
  } finally {
    statsLoading.value = false
  }
}

const goToSettings = () => router.push({ path: '/settings', hash: '#health-profile' })
const goToGlucoseRecord = () => router.push('/glucose-record')
const goToAssistant = () =>
  router.push({ path: '/assistant', query: { prefill: '请解读我的健康档案和最近血糖概况' } })

onMounted(() => {
  void loadProfile()
  void loadWeeklyStats()
})

defineExpose({ refreshProfile: loadProfile, refreshWeeklyStats: loadWeeklyStats })
</script>

<style scoped>
.user-profile-card {
  margin-bottom: 20px;
  border-top: 3px solid #409eff;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-header > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.card-header > div > span {
  color: #303133;
  font-weight: 600;
}

.card-header small,
.weekly-heading span {
  color: #909399;
  font-size: 12px;
}

.inline-alert {
  margin-bottom: 14px;
}

.identity-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.identity-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.identity-copy strong {
  overflow: hidden;
  color: #303133;
  font-size: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.identity-copy span {
  overflow: hidden;
  color: #909399;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.profile-item {
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f5f7fa;
}

.profile-item span,
.weekly-stat span {
  display: block;
  margin-bottom: 4px;
  color: #909399;
  font-size: 12px;
}

.profile-item strong {
  display: block;
  overflow: hidden;
  color: #303133;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-guidance {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 10px;
  color: #8a5a00;
  background: #fdf6ec;
  font-size: 13px;
}

.weekly-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.weekly-heading > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.weekly-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.weekly-stat {
  padding: 12px 8px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  text-align: center;
}

.weekly-stat strong {
  display: block;
  color: #409eff;
  font-size: 19px;
}

.weekly-status {
  max-width: 100%;
  height: auto;
  margin-top: 12px;
  padding-top: 5px;
  padding-bottom: 5px;
  white-space: normal;
}

.compact-empty {
  padding: 8px 0 2px;
}

.card-actions {
  display: flex;
  gap: 10px;
  margin-top: 18px;
}

.card-actions .el-button {
  flex: 1;
  margin-left: 0;
}

@media (max-width: 480px) {
  .identity-row {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .identity-copy {
    min-width: calc(100% - 74px);
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .weekly-grid {
    grid-template-columns: 1fr;
  }

  .card-actions {
    flex-direction: column;
  }
}
</style>
