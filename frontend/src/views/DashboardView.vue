<template>
  <div class="dashboard-container dashboard-container--dense">
    <section class="welcome-panel welcome-panel--dense">
      <div class="welcome-copy">
        <h2>您好，{{ userName }}</h2>
        <p class="welcome-sub">{{ currentDate }} · 今日概览</p>
      </div>
      <div class="welcome-actions">
        <el-button type="primary" size="small" @click="openGlucoseDrawer">记录血糖</el-button>
        <el-button plain size="small" @click="goToAssistant">咨询助理</el-button>
        <el-button
          text
          type="primary"
          size="small"
          @click="router.push({ path: '/assistant', query: { prefill: '本周血糖统计' } })"
        >
          解读本周
        </el-button>
      </div>
    </section>

    <div class="dashboard-body">
      <div class="dashboard-main">
        <el-card class="chart-card chart-card--dense" :class="{ 'is-empty': !loading && !hasGlucoseData }" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="card-title-block">
                <span>血糖趋势</span>
              </div>
              <div class="header-actions">
                <el-button size="small" circle @click="refreshData">
                  <el-icon><Refresh /></el-icon>
                </el-button>
                <el-button size="small" plain @click="openGlucoseDrawer">记一笔</el-button>
                <el-radio-group v-model="glucosePeriod" size="small">
                  <el-radio-button label="week">周</el-radio-button>
                  <el-radio-button label="month">月</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div v-if="loading" class="loading-container chart-loading">
            <el-skeleton :rows="2" animated />
          </div>
          <div v-else-if="!hasGlucoseData" class="empty-data chart-empty">
            <div class="inline-empty">
              <p>还没有血糖数据</p>
              <el-button type="primary" size="small" @click="openGlucoseDrawer">记录血糖</el-button>
            </div>
          </div>
          <div v-else class="chart-container chart-container--dense">
            <div ref="glucoseChartRef" class="chart" :key="chartKey"></div>
          </div>
        </el-card>

        <!-- 健康指标：一行条，不再单独大卡 -->
        <div class="metric-strip">
          <div class="metric-strip-item">
            <span>体重</span>
            <strong>{{ healthMetrics.weight || '--' }} <small>kg</small></strong>
          </div>
          <div class="metric-strip-item">
            <span>血压</span>
            <strong>{{ healthMetrics.bloodPressure || '--' }}</strong>
          </div>
          <div class="metric-strip-item">
            <span>BMI</span>
            <strong>{{ healthMetrics.bmi || '--' }}</strong>
          </div>
          <div class="metric-strip-item">
            <span>步数</span>
            <strong>{{ healthMetrics.steps || '--' }}</strong>
          </div>
          <el-button class="metric-strip-more" text type="primary" size="small" @click="goToHealthData">
            健康数据
          </el-button>
        </div>

        <!-- 入口：一行三块，无大卡片堆叠 -->
        <div class="entry-rail">
          <button type="button" class="entry-chip" @click="goToDietRecord">
            <strong>今日饮食</strong>
            <span v-if="hasDietData">{{ dietRecords.length }} 餐 · 去管理</span>
            <span v-else>去记录</span>
          </button>
          <button type="button" class="entry-chip" @click="goToDietRecord">
            <strong>饮食建议</strong>
            <span v-if="hasDietSuggestions">{{ dietSuggestionPreview }}</span>
            <span v-else>去饮食页查看</span>
          </button>
          <button
            type="button"
            class="entry-chip"
            @click="hasAnalysisData ? showFullAdvice() : fetchGlucoseAnalysis()"
          >
            <strong>智能分析</strong>
            <span v-if="hasAnalysisData">{{ riskAssessmentStatus.title }} · 查看</span>
            <span v-else>{{ loadingAnalysis ? '分析中…' : '生成 / 问助理' }}</span>
          </button>
        </div>
      </div>

      <aside class="dashboard-aside">
        <UserProfileCard dense @record-glucose="openGlucoseDrawer" />

        <!-- 提醒：默认折叠，只占一行 -->
        <div class="collapse-row" @click="remindersExpanded = !remindersExpanded">
          <div class="collapse-row-main">
            <strong>今日提醒</strong>
            <el-tag size="small" effect="plain">{{ reminderDoneCount }}/{{ reminders.length }}</el-tag>
          </div>
          <el-button text type="primary" size="small" @click.stop="remindersExpanded = !remindersExpanded">
            {{ remindersExpanded ? '收起' : '展开' }}
          </el-button>
        </div>
        <div v-if="remindersExpanded" class="reminder-panel">
          <div v-for="reminder in reminders" :key="reminder.id" class="reminder-item">
            <div class="reminder-content">
              <div class="reminder-text">{{ reminder.text }}</div>
              <div class="reminder-time">{{ reminder.time }}</div>
            </div>
            <el-checkbox v-model="reminder.done" @change="updateReminder(reminder)" @click.stop />
          </div>
        </div>

        <!-- 快捷入口：胶囊按钮，避免裸文字链 -->
        <section class="quick-nav" aria-label="快捷入口">
          <div class="quick-nav-label">快捷入口</div>
          <div class="quick-nav-list">
            <button type="button" class="quick-nav-item" @click="goToGlucoseList">
              <el-icon><DataAnalysis /></el-icon>
              <span>血糖记录</span>
            </button>
            <button type="button" class="quick-nav-item" @click="goToDietRecord">
              <el-icon><Bowl /></el-icon>
              <span>饮食管理</span>
            </button>
            <button type="button" class="quick-nav-item" @click="router.push('/knowledge')">
              <el-icon><Reading /></el-icon>
              <span>知识库</span>
            </button>
            <button type="button" class="quick-nav-item" @click="router.push('/settings')">
              <el-icon><Setting /></el-icon>
              <span>设置</span>
            </button>
            <button
              type="button"
              class="quick-nav-item quick-nav-item--accent"
              @click="router.push({ path: '/assistant', query: { prefill: '请解读我最近的血糖' } })"
            >
              <el-icon><ChatLineRound /></el-icon>
              <span>问助理</span>
            </button>
          </div>
        </section>
      </aside>
    </div>

    <el-drawer
      v-model="glucoseDrawerVisible"
      title="快速记录血糖"
      direction="rtl"
      size="400px"
      append-to-body
      destroy-on-close
    >
      <div class="glucose-drawer">
        <p class="drawer-hint">保存后会刷新首页趋势。完整表单也可在「血糖记录」页填写。</p>
        <el-form :model="glucoseForm" label-position="top" class="compact-form">
          <el-form-item label="血糖值 (mmol/L)">
            <el-input-number
              v-model="glucoseForm.value"
              :min="1"
              :max="30"
              :precision="1"
              :step="0.1"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="测量类型">
            <el-select v-model="glucoseForm.measurement_time" placeholder="请选择" style="width: 100%">
              <el-option label="早餐前" value="BEFORE_BREAKFAST" />
              <el-option label="早餐后" value="AFTER_BREAKFAST" />
              <el-option label="午餐前" value="BEFORE_LUNCH" />
              <el-option label="午餐后" value="AFTER_LUNCH" />
              <el-option label="晚餐前" value="BEFORE_DINNER" />
              <el-option label="晚餐后" value="AFTER_DINNER" />
              <el-option label="睡前" value="BEFORE_SLEEP" />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="drawer-actions">
          <el-button @click="glucoseDrawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="importing" @click="importGlucoseData">保存记录</el-button>
        </div>
        <el-button text type="primary" @click="goToGlucoseRecord">打开完整记录页</el-button>
      </div>
    </el-drawer>

    <div v-if="showFullAnalysisCard" class="modal-overlay">
      <el-card class="full-analysis-card modal-card">
        <template #header>
          <div class="card-header">
            <span>血糖风险评估与管理建议</span>
            <el-button type="danger" circle plain @click="showFullAnalysisCard = false">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>
        <div class="advice-content-wrapper" v-html="fullAnalysisContent"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onActivated, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  Bowl,
  ChatLineRound,
  ChatLineSquare,
  CircleCheck,
  Clock,
  Close,
  DataAnalysis,
  InfoFilled,
  Plus,
  Reading,
  Refresh,
  Setting,
  Warning,
  WarningFilled
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { glucoseApi, healthApi, dietApi, knowledgeApi, apiClient } from '../api'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import UserProfileCard from '../components/UserProfileCard.vue'

const detailedAdviceContent = ref('')
const showDetailedAdviceCard = ref(false)

// 新增：用于"查看完整分析"模态框的状态
const fullAnalysisContent = ref('')
const showFullAnalysisCard = ref(false)

// 定义血糖记录类型接口
interface GlucoseRecord {
  id: string;
  value: number;
  measured_at: string;
  measurement_time: string;
  notes: string;
  user_id: string;
}

// 定义日期分组记录类型
interface DateGroupedRecords {
  [date: string]: {
    fasting: number[];
    afterMeal: number[];
  }
}

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const importing = ref(false)
const glucosePeriod = ref('week')
const glucoseChartRef = ref<HTMLElement | null>(null)
const glucoseChart = ref<echarts.ECharts | null>(null)
const chartKey = ref(0)
const glucoseCheckTimer = ref<number | null>(null)

const userName = computed(() => userStore.userFullName)
const currentDate = computed(() => dayjs().format('YYYY年MM月DD日'))

// 模拟数据
const healthMetrics = ref({
  weight: '68.5',
  bloodPressure: '120/80',
  bmi: '22.5',
  steps: '6,842'
})

const hasGlucoseData = ref(false)
const hasDietData = ref(true)
const glucoseAlerts = ref<Array<{title: string, message: string, type: 'success' | 'warning' | 'info' | 'error'}>>([])

const dietRecords = ref([
  { time: '早餐 08:30', name: '全麦面包+牛奶+鸡蛋', calories: 350 },
  { time: '午餐 12:00', name: '糙米饭+清蒸鱼+西兰花', calories: 480 },
  { time: '晚餐 18:30', name: '蔬菜沙拉+鸡胸肉', calories: 420 }
])

const reminders = ref([
  { id: 1, text: '测量空腹血糖', time: '早上8:00', done: true },
  { id: 2, text: '服用二甲双胍', time: '早餐后', done: true },
  { id: 3, text: '测量餐后血糖', time: '午餐后2小时', done: false },
  { id: 4, text: '30分钟有氧运动', time: '下午5:00', done: false },
  { id: 5, text: '服用二甲双胍', time: '晚餐后', done: false }
])

const knowledgeArticles = ref([
  {
    id: 1,
    title: '糖尿病患者如何科学运动',
    description: '适当的运动可以帮助控制血糖，但糖尿病患者需要注意一些事项...'
  },
  {
    id: 2,
    title: '低血糖的识别与处理',
    description: '低血糖是糖尿病患者常见的急性并发症，及时识别和处理非常重要...'
  },
  {
    id: 3,
    title: '糖尿病饮食的"四多四少"原则',
    description: '合理的饮食对控制血糖至关重要，建议多吃蔬菜、粗粮，少吃...'
  }
])

// 血糖数据
const glucoseRecords = ref<GlucoseRecord[]>([])

// 快速导入血糖表单（抽屉）
const glucoseDrawerVisible = ref(false)
const glucoseForm = ref({
  value: 5.6,
  measurement_time: 'BEFORE_BREAKFAST'
})
const remindersExpanded = ref(false) // 默认折叠，再压一屏

const openGlucoseDrawer = () => {
  glucoseDrawerVisible.value = true
}

const reminderDoneCount = computed(() => reminders.value.filter((item) => item.done).length)
const dietSuggestionPreview = computed(() => {
  const text = dietSuggestions.value.quick_suggestion || dietSuggestions.value.current_status || ''
  if (!text) return '去饮食页'
  return text.length > 18 ? `${text.slice(0, 18)}…` : text
})

// 智能分析相关状态
const loadingAnalysis = ref(false)
const hasAnalysisData = ref(false)
const glucoseAnalysis = ref({
  statistics: {
    average: 0,
    max: 0,
    min: 0,
    std: 0,
    in_range_percentage: 0,
    high_percentage: 0,
    low_percentage: 0
  },
  patterns: {},
  advice: '',
  risk_level: 'normal', // 新增风险等级: normal, warning, danger
  record_count: 0,
  updated_at: ''
})

// 饮食建议相关状态
const loadingDietSuggestions = ref(false)
const hasDietSuggestions = ref(false)
const selectedMealType = ref('breakfast')
const dietSuggestions = ref({
  current_status: '',
  glucose_status: 'normal', // 可能的值: high, normal, low
  quick_suggestion: '',
  recommended_foods: [] as string[],
  foods_to_avoid: [] as string[],
  meal_plan_example: ''
})

// 新增：风险评估状态计算属性
const riskAssessmentStatus = computed(() => {
  const level = glucoseAnalysis.value.risk_level
  if (level === 'danger') {
    return {
      class: 'ai-alert-danger',
      icon: WarningFilled,
      title: 'AI血糖高风险评估'
    }
  }
  if (level === 'warning') {
    return {
      class: 'ai-alert-warning',
      icon: Warning,
      title: 'AI血糖风险预警'
    }
  }
  return {
    class: 'ai-alert-good',
    icon: CircleCheck,
    title: 'AI血糖健康评估'
  }
})

// 从API获取血糖数据
const fetchGlucoseData = async () => {
  try {
    loading.value = true
    console.log('开始获取血糖数据...')
    
    // 使用新的API函数
    const response = await glucoseApi.getRecentGlucoseRecords(
      glucosePeriod.value === 'week' ? 7 : 30
    )
    
    console.log('获取到血糖数据:', response.data)
    
    if (Array.isArray(response.data)) {
      glucoseRecords.value = response.data
      hasGlucoseData.value = glucoseRecords.value.length > 0
      
      console.log(`获取到 ${glucoseRecords.value.length} 条血糖记录`)
      console.log('血糖记录示例:', glucoseRecords.value.slice(0, 2))
      
      // 返回数据状态，不在此函数中初始化图表
      return {
        success: true,
        hasData: hasGlucoseData.value
      }
    } else {
      console.error('API返回的数据格式不正确:', response.data)
      hasGlucoseData.value = false
      return {
        success: false,
        hasData: false
      }
    }
  } catch (error) {
    console.error('获取血糖数据失败', error)
    hasGlucoseData.value = false
    return {
      success: false,
      hasData: false
    }
  } finally {
    loading.value = false
  }
}

// 处理血糖数据，根据周期返回图表所需数据
const processGlucoseData = () => {
  console.log('开始处理血糖数据，当前记录数:', glucoseRecords.value?.length || 0)
  
  if (!glucoseRecords.value || glucoseRecords.value.length === 0) {
    console.log('没有血糖记录，返回空数据')
    return {
      dates: [] as string[],
      fastingData: [] as (number | null)[],
      afterMealData: [] as (number | null)[]
    }
  }
  
  // 根据周期过滤数据
  let filteredRecords = [...glucoseRecords.value]
  const now = dayjs()
  
  if (glucosePeriod.value === 'week') {
    // 获取最近7天的数据
    const startDate = now.subtract(6, 'day').startOf('day')
    console.log('周视图起始日期:', startDate.format('YYYY-MM-DD'))
    filteredRecords = filteredRecords.filter(record => 
      dayjs(record.measured_at).isAfter(startDate)
    )
  } else {
    // 获取最近30天的数据
    const startDate = now.subtract(29, 'day').startOf('day')
    console.log('月视图起始日期:', startDate.format('YYYY-MM-DD'))
    filteredRecords = filteredRecords.filter(record => 
      dayjs(record.measured_at).isAfter(startDate)
    )
  }
  
  console.log('过滤后的记录数:', filteredRecords.length)
  
  // 按日期分组
  const recordsByDate: DateGroupedRecords = {}
  const dateFormat = 'MM-DD'
  
  filteredRecords.forEach(record => {
    const date = dayjs(record.measured_at).format(dateFormat)
    if (!recordsByDate[date]) {
      recordsByDate[date] = {
        fasting: [],
        afterMeal: []
      }
    }
    
    // 根据测量时间类型分组
    if (['BEFORE_BREAKFAST', 'BEFORE_LUNCH', 'BEFORE_DINNER', 'before_breakfast', 'before_lunch', 'before_dinner'].includes(record.measurement_time.toUpperCase())) {
      recordsByDate[date].fasting.push(record.value)
    } else if (['AFTER_BREAKFAST', 'AFTER_LUNCH', 'AFTER_DINNER', 'after_breakfast', 'after_lunch', 'after_dinner'].includes(record.measurement_time.toUpperCase())) {
      recordsByDate[date].afterMeal.push(record.value)
    }
  })
  
  console.log('按日期分组后的数据:', recordsByDate)
  
  // 准备图表数据
  const dates: string[] = []
  const fastingData: (number | null)[] = []
  const afterMealData: (number | null)[] = []
  
  // 生成日期范围
  let dateRange: string[] = []
  if (glucosePeriod.value === 'week') {
    // 最近7天
    for (let i = 6; i >= 0; i--) {
      dateRange.push(now.subtract(i, 'day').format(dateFormat))
    }
  } else {
    // 最近30天
    for (let i = 29; i >= 0; i--) {
      dateRange.push(now.subtract(i, 'day').format(dateFormat))
    }
  }
  
  // 修复：使用新的dayjs实例避免日期计算错误
  dateRange = []
  const periodDays = glucosePeriod.value === 'week' ? 7 : 30
  const startDay = glucosePeriod.value === 'week' ? 6 : 29
  
  for (let i = startDay; i >= 0; i--) {
    const d = dayjs().subtract(i, 'day')
    dateRange.push(d.format(dateFormat))
  }
  
  console.log('生成的日期范围:', dateRange)
  
  // 填充数据，没有的日期用null
  dateRange.forEach(date => {
    dates.push(date)
    
    if (recordsByDate[date]) {
      // 计算空腹血糖平均值
      const fastingValues = recordsByDate[date].fasting
      fastingData.push(fastingValues.length > 0 
        ? Number((fastingValues.reduce((sum, val) => sum + val, 0) / fastingValues.length).toFixed(1))
        : null)
      
      // 计算餐后血糖平均值
      const afterMealValues = recordsByDate[date].afterMeal
      afterMealData.push(afterMealValues.length > 0
        ? Number((afterMealValues.reduce((sum, val) => sum + val, 0) / afterMealValues.length).toFixed(1))
        : null)
    } else {
      fastingData.push(null)
      afterMealData.push(null)
    }
  })
  
  console.log('处理后的图表数据:', {
    dates,
    fastingData,
    afterMealData
  })
  
  return { dates, fastingData, afterMealData }
}

// 快速导入血糖数据
const importGlucoseData = async () => {
  // 验证表单
  if (!glucoseForm.value.value || !glucoseForm.value.measurement_time) {
    ElMessage.warning('请填写完整的血糖数据')
    return
  }
  
  try {
    importing.value = true
    
    // 打印 userStore 以检查用户 ID 字段
    console.log('userStore:', userStore)
    
    // 检查用户ID是否存在
    if (!userStore.user || !userStore.user.id) {
      ElMessage.error('用户未登录或用户ID不存在')
      importing.value = false
      return
    }
    
    // 构建请求数据 - 确保格式正确
    const data = {
      value: glucoseForm.value.value,
      measured_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
      measurement_time: glucoseForm.value.measurement_time,
      measurement_method: 'FINGER_STICK', // 默认使用指尖血
      notes: '', // 添加可选的备注字段
      user_id: userStore.user.id // 添加用户ID
    }
    
    console.log('发送的血糖数据:', data)
    
    // 调用API保存血糖数据
    const response = await apiClient.post('/api/v1/glucose', data)
    
    console.log('保存血糖数据响应:', response)
    
    ElMessage.success('血糖数据保存成功')

    // 重置表单并关闭抽屉
    glucoseForm.value.value = 5.6
    glucoseDrawerVisible.value = false

    // 刷新血糖数据
    await fetchGlucoseData()

    // 分析血糖数据
    await analyzeGlucoseData()

    // 获取三天分析
    await fetchGlucoseAnalysis()
  } catch (error) {
    console.error('保存血糖数据失败:', error)
    
    // 提供更详细的错误信息
    if (error.response) {
      console.error('错误响应数据:', error.response.data)
      
      // 显示详细的验证错误信息
      if (error.response.data && error.response.data.detail) {
        let errorMsg = '数据验证失败: ';
        
        if (Array.isArray(error.response.data.detail)) {
          errorMsg += error.response.data.detail.map(err => `${err.loc.join('.')}:${err.msg}`).join('; ');
        } else {
          errorMsg += error.response.data.detail;
        }
        
        ElMessage.error(errorMsg)
        return;
      }
    }
    
    ElMessage.error('保存血糖数据失败，请稍后再试')
  } finally {
    importing.value = false
  }
}

// 分析血糖数据
const analyzeGlucoseData = async () => {
  try {
    // 获取最近的血糖数据
    const recentResponse = await glucoseApi.getRecentGlucoseRecords(1); // 获取最近1天的数据
    
    if (!recentResponse.data || recentResponse.data.length === 0) {
      console.log('没有最近的血糖数据可供分析');
      return null;
    }
    
    const records = recentResponse.data;
    console.log('获取到最近的血糖数据:', records);
    
    // 调用后端分析API获取血糖异常预警
    try {
      const analyzeResponse = await apiClient.post('/api/v1/glucose-monitor/analyze', {
        hours: 24 // 分析最近24小时的数据
      }, {
        timeout: 20000 // 设置20秒超时时间
      });
      
      // 处理API返回的预警信息
      if (analyzeResponse.data?.has_alerts) {
        // 如果有预警信息并且包含大模型生成的警报消息
        if (analyzeResponse.data.alert_message) {
          // 清除现有的相似警报
          glucoseAlerts.value = glucoseAlerts.value.filter(alert => !alert.title.includes('血糖异常'));
          
          // 添加新的警报，显示大模型生成的个性化预警信息
          addAlert(
            '血糖异常预警', 
            analyzeResponse.data.alert_message, 
            analyzeResponse.data.alerts.some(a => a.severity === 'high') ? 'error' : 'warning'
          );
          console.log('添加大模型生成的预警消息:', analyzeResponse.data.alert_message);
          
          return {
            statistics: analyzeResponse.data.statistics || {
              average: 0,
              max: 0,
              min: 0,
              count: records.length,
              high_count: 0,
              low_count: 0
            },
            has_alerts: true,
            alert_message: analyzeResponse.data.alert_message
          };
        }
      }
    } catch (apiError) {
      console.error('调用血糖分析API失败，回退到本地分析:', apiError);
      // 发生错误时继续使用本地分析
    }
    
    // 本地分析血糖数据（作为备选方案）
    const highThreshold = 7.8; // 高血糖阈值
    const lowThreshold = 3.9; // 低血糖阈值
    
    const highRecords = records.filter(record => record.value > highThreshold);
    const lowRecords = records.filter(record => record.value < lowThreshold);
    
    // 生成警报
    if (highRecords.length > 0 || lowRecords.length > 0) {
      let alertMessage = '';
      
      if (highRecords.length > 0) {
        const latestHigh = highRecords.sort((a, b) => 
          new Date(b.measured_at).getTime() - new Date(a.measured_at).getTime()
        )[0];
        
        alertMessage += `检测到${highRecords.length}次高血糖记录，最近一次为${dayjs(latestHigh.measured_at).format('MM-DD HH:mm')}，血糖值${latestHigh.value.toFixed(1)}mmol/L。`;
      }
      
      if (lowRecords.length > 0) {
        if (alertMessage) alertMessage += ' ';
        
        const latestLow = lowRecords.sort((a, b) => 
          new Date(b.measured_at).getTime() - new Date(a.measured_at).getTime()
        )[0];
        
        alertMessage += `检测到${lowRecords.length}次低血糖记录，最近一次为${dayjs(latestLow.measured_at).format('MM-DD HH:mm')}，血糖值${latestLow.value.toFixed(1)}mmol/L。`;
      }
      
      // 添加警报
      if (alertMessage) {
        addAlert('血糖异常提醒', alertMessage, 'warning');
      }
    }
    
    // 计算统计数据
    const sum = records.reduce((acc, record) => acc + record.value, 0);
    const avg = sum / records.length;
    const max = Math.max(...records.map(record => record.value));
    const min = Math.min(...records.map(record => record.value));
    
    return {
      statistics: {
        average: avg,
        max: max,
        min: min,
        count: records.length,
        high_count: highRecords.length,
        low_count: lowRecords.length
      },
      has_alerts: highRecords.length > 0 || lowRecords.length > 0
    };
  } catch (error) {
    console.error('分析血糖数据失败:', error);
    return null;
  }
}

// 添加警报
const addAlert = (title: string, message: string, type: 'success' | 'warning' | 'info' | 'error' = 'warning') => {
  glucoseAlerts.value.push({
    title,
    message,
    type
  })
}

// 移除警报
const removeAlert = (index: number) => {
  glucoseAlerts.value.splice(index, 1)
}

// 组件挂载时初始化
onMounted(async () => {
  try {
    // 获取血糖数据
    const glucoseResult = await fetchGlucoseData()
    
    // 如果有血糖数据，分析血糖数据
    if (glucoseResult?.hasData) {
      await analyzeGlucoseData()
      await fetchGlucoseAnalysis()
    }
    
    // 确保DOM已更新
    await nextTick()
    
    // 初始化图表
    if (hasGlucoseData.value) {
      initGlucoseChart()
    }
    
    // 设置定时检查血糖数据的定时器（每30分钟检查一次）
    const checkInterval = 30 * 60 * 1000; // 30分钟
    glucoseCheckTimer.value = setInterval(async () => {
      console.log('定时检查血糖数据...');
      await analyzeGlucoseData();
    }, checkInterval);
    
    // 如果有血糖数据，获取饮食建议
    if (glucoseResult?.hasData) {
      await fetchDietSuggestions()
    }
    
  } catch (error) {
    console.error('初始化数据失败:', error)
    ElMessage.error('加载数据失败，请刷新页面重试')
  } finally {
    loading.value = false
  }
})

// 在组件卸载时清除定时器
onUnmounted(() => {
  if (glucoseCheckTimer.value) {
    clearInterval(glucoseCheckTimer.value);
    glucoseCheckTimer.value = null;
  }
})

// 添加onActivated钩子，在组件被激活时重新获取数据
onActivated(async () => {
  console.log('Dashboard组件被激活，重新获取数据')
  try {
    // 检查图表是否已初始化
    if (hasGlucoseData.value && !glucoseChart.value && glucoseChartRef.value) {
      console.log('组件激活，但图表未初始化，尝试初始化图表')
      
      // 更新chartKey强制重新渲染图表容器
      chartKey.value += 1
      
      await nextTick()
      
      // 强制设置容器尺寸
      if (glucoseChartRef.value) {
        glucoseChartRef.value.style.height = '300px'
        glucoseChartRef.value.style.width = '100%'
      }
      
      setTimeout(() => {
        initGlucoseChart()
      }, 200)
    } else if (!glucoseChart.value) {
      // 重新获取数据
      const result = await fetchGlucoseData()
      
      if (result.success && result.hasData) {
        // 更新chartKey强制重新渲染图表容器
        chartKey.value += 1
        
        await nextTick()
        
        // 强制设置容器尺寸
        if (glucoseChartRef.value) {
          glucoseChartRef.value.style.height = '300px'
          glucoseChartRef.value.style.width = '100%'
        }
        
        setTimeout(() => {
          initGlucoseChart()
        }, 200)
      }
    } else {
      console.log('图表已存在，尝试更新')
      updateGlucoseChart()
    }
    
    // 刷新饮食建议
    if (hasGlucoseData.value && !hasDietSuggestions.value) {
      await fetchDietSuggestions()
    }
  } catch (error) {
    console.error('重新获取血糖数据失败', error)
  } finally {
    loading.value = false
  }
})

// 添加手动刷新功能
const refreshData = async () => {
  try {
    loading.value = true
    console.log('手动刷新数据开始')
    
    // 销毁现有图表实例
    if (glucoseChart.value) {
      console.log('销毁现有图表实例')
      glucoseChart.value.dispose()
      glucoseChart.value = null
    }
    
    // 更新chartKey强制重新渲染图表容器
    chartKey.value += 1
    console.log('更新chartKey:', chartKey.value)
    
    // 获取新数据
    const result = await fetchGlucoseData()
    
    // 确保在获取数据后重新创建图表
    if (result.success && result.hasData) {
      console.log('刷新后准备重新创建图表')
      
      // 使用更简单的方法，直接重新创建图表
      await nextTick()
      
      // 确保图表容器存在
      if (!glucoseChartRef.value) {
        console.error('图表容器不存在，无法重新创建图表')
        return
      }
      
      // 强制设置容器尺寸
      glucoseChartRef.value.style.height = '300px'
      glucoseChartRef.value.style.width = '100%'
      
      console.log('重新创建图表实例')
      try {
        // 确保echarts已正确导入
        if (!echarts) {
          console.error('echarts库未正确导入')
          return
        }
        
        // 直接创建新实例
        glucoseChart.value = echarts.init(glucoseChartRef.value)
        console.log('图表实例创建成功:', glucoseChart.value)
        
        // 设置图表选项
        updateGlucoseChart()
      } catch (error) {
        console.error('刷新时创建图表实例失败:', error)
      }
    }
    
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败', error)
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

// 监听glucosePeriod变化，更新图表
watch(glucosePeriod, () => {
  if (hasGlucoseData.value && glucoseChart.value) {
    updateGlucoseChart()
  }
})

// 更新血糖图表
const updateGlucoseChart = () => {
  console.log('开始更新图表')
  if (!glucoseChart.value) {
    console.error('图表实例不存在，无法更新')
    return
  }
  
  const { dates, fastingData, afterMealData } = processGlucoseData()
  console.log('处理后的图表数据:', { 
    dates, 
    fastingData, 
    afterMealData,
    datesLength: dates.length
  })
  
  try {
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params: any) {
          let result = params[0].axisValueLabel + '<br/>';
          params.forEach((param: any) => {
            if (param.value !== null) {
              const color = param.value > 7.8 ? '#f56c6c' : 
                            param.value < 3.9 ? '#e6a23c' : '#67c23a';
              result += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>`;
              result += `${param.seriesName}: <span style="color:${color};font-weight:bold">${param.value} mmol/L</span><br/>`;
            }
          });
          return result;
        }
      },
      legend: {
        data: ['空腹血糖', '餐后血糖']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '血糖 (mmol/L)',
        min: 3, // 调整范围以获得更好的视觉效果
        max: 12,
        interval: 1.5,
        axisLine: { lineStyle: { color: '#aaa' } },
        splitLine: {
          lineStyle: {
            color: '#eee'
          }
        }
      },
      series: [
        {
          name: '空腹血糖',
          type: 'line',
          smooth: true, // 使线条更平滑
          data: fastingData,
          connectNulls: true,
          symbol: 'circle',
          symbolSize: 8, // 稍大的标记点
          itemStyle: {
            color: '#3498db' // 活力蓝
          },
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(52, 152, 219, 0.5)',
            shadowBlur: 10,
            shadowOffsetY: 5
          },
          markArea: {
            itemStyle: {
              color: 'rgba(46, 204, 113, 0.1)' // 清新绿
            },
            data: [
              [{
                yAxis: 3.9
              }, {
                yAxis: 6.1
              }]
            ]
          }
        },
        {
          name: '餐后血糖',
          type: 'line',
          smooth: true, // 使线条更平滑
          data: afterMealData,
          connectNulls: true,
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: {
            color: '#e67e22' // 活力橙
          },
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(230, 126, 34, 0.5)',
            shadowBlur: 10,
            shadowOffsetY: 5
          },
          markArea: {
            itemStyle: {
              color: 'rgba(46, 204, 113, 0.1)' // 清新绿
            },
            data: [
              [{
                yAxis: 3.9
              }, {
                yAxis: 7.8
              }]
            ]
          }
        }
      ]
    }
    
    console.log('设置图表选项')
    glucoseChart.value.setOption(option)
    console.log('图表选项设置完成')
  } catch (error) {
    console.error('设置图表选项失败:', error)
  }
}

const initGlucoseChart = () => {
  console.log('开始初始化图表')
  console.log('glucoseChartRef元素:', glucoseChartRef.value)
  
  if (!glucoseChartRef.value) {
    console.error('图表容器元素不存在，无法初始化图表')
    return
  }
  
  // 如果已经有图表实例，先销毁
  if (glucoseChart.value) {
    console.log('销毁旧图表实例')
    try {
      glucoseChart.value.dispose()
    } catch (error) {
      console.error('销毁旧图表实例失败:', error)
    }
    glucoseChart.value = null
  }
  
  // 确保DOM元素有宽高
  const chartElement = glucoseChartRef.value
  if (chartElement.offsetHeight === 0) {
    console.log('图表容器高度为0，设置默认高度')
    chartElement.style.height = '300px'
  }
  
  if (chartElement.offsetWidth === 0) {
    console.log('图表容器宽度为0，设置默认宽度')
    chartElement.style.width = '100%'
  }
  
  console.log('图表容器尺寸:', {
    height: chartElement.offsetHeight,
    width: chartElement.offsetWidth,
    clientHeight: chartElement.clientHeight,
    clientWidth: chartElement.clientWidth
  })
  
  // 创建新的图表实例
  try {
    console.log('创建新图表实例')
    // 确保echarts已正确导入
    if (!echarts) {
      console.error('echarts库未正确导入')
      return
    }
    
    glucoseChart.value = echarts.init(chartElement)
    console.log('图表实例创建成功:', glucoseChart.value)
    
    // 设置图表选项
    updateGlucoseChart()
    
    // 监听窗口大小变化，调整图表大小
    const resizeHandler = () => {
      console.log('窗口大小变化，调整图表大小')
      if (glucoseChart.value) {
        glucoseChart.value.resize()
      }
    }
    
    window.removeEventListener('resize', resizeHandler)
    window.addEventListener('resize', resizeHandler)
  } catch (error) {
    console.error('图表初始化失败:', error)
    // 尝试再次初始化
    setTimeout(() => {
      console.log('尝试再次初始化图表')
      try {
        if (chartElement && !glucoseChart.value) {
          glucoseChart.value = echarts.init(chartElement)
          updateGlucoseChart()
        }
      } catch (retryError) {
        console.error('再次初始化图表失败:', retryError)
      }
    }, 500)
  }
}

const updateReminder = (reminder: any) => {
  // 这里应该调用API更新提醒状态
  console.log('更新提醒状态', reminder)
}

const readArticle = (id: number) => {
  router.push(`/knowledge/${id}`)
}

const goToGlucoseRecord = () => {
  glucoseDrawerVisible.value = false
  router.push('/glucose-record')
}

const goToGlucoseList = () => {
  router.push('/glucose')
}

const goToAssistant = () => {
  router.push('/assistant')
}

const goToHealthData = () => {
  router.push('/health')
}

const goToDietRecord = () => {
  router.push('/diet')
}

// 获取血糖智能分析
const fetchGlucoseAnalysis = async () => {
  if (!hasGlucoseData.value) return

  try {
    loadingAnalysis.value = true
    
    // 获取最近记录的血糖数据
    const recentResponse = await glucoseApi.getRecentGlucoseRecords(3)
    
    if (!recentResponse.data || recentResponse.data.length < 3) {
      hasAnalysisData.value = false
      loadingAnalysis.value = false
      return
    }
    
    // 使用后端分析API获取血糖异常预警和统计数据
    const analyzeResponse = await apiClient.post('/api/v1/glucose-monitor/analyze', {
      hours: 72 // 分析最近72小时(3天)的数据
    }, {
      timeout: 30000 // 设置30秒超时时间
    })
    
    // 确定风险等级
    let riskLevel: 'normal' | 'warning' | 'danger' = 'normal'
    if (analyzeResponse.data?.has_alerts && analyzeResponse.data.alerts?.length > 0) {
      if (analyzeResponse.data.alerts.some(a => a.severity === 'high')) {
        riskLevel = 'danger'
      } else {
        riskLevel = 'warning'
      }
    }
    
    // 如果有预警信息，显示在顶部警报区域
    if (analyzeResponse.data?.has_alerts && analyzeResponse.data?.alert_message) {
      // 清除现有的相似警报
      glucoseAlerts.value = glucoseAlerts.value.filter(alert => !alert.title.includes('血糖异常'))
      
      // 添加新的警报，显示大模型生成的个性化预警信息
      addAlert(
        '血糖异常预警', 
        analyzeResponse.data.alert_message, 
        analyzeResponse.data.alerts.some(a => a.severity === 'high') ? 'error' : 'warning'
      )
    }
    
    // 获取统计数据
    const statsResponse = await glucoseApi.getStatistics('week')
    
    if (statsResponse.data) {
      // 构建分析数据结构
      const records = recentResponse.data
      const stats = statsResponse.data
      
      // 计算标准差
      let sum = 0
      let sumSquares = 0
      records.forEach(record => {
        sum += record.value
        sumSquares += record.value * record.value
      })
      const mean = sum / records.length
      const variance = sumSquares / records.length - mean * mean
      const std = Math.sqrt(variance)
      
      // 计算达标率
      const inRangeCount = records.filter(r => r.value >= 3.9 && r.value <= 7.8).length
      const inRangePercentage = (inRangeCount / records.length) * 100
      
      // 计算高低血糖比例
      const highCount = records.filter(r => r.value > 7.8).length
      const lowCount = records.filter(r => r.value < 3.9).length
      const highPercentage = (highCount / records.length) * 100
      const lowPercentage = (lowCount / records.length) * 100
      
      // 优先使用大模型生成的建议
      let advice = ''
      
      // 判断是否有可用的大模型生成的建议
      if (analyzeResponse.data?.alert_message) {
        // 使用大模型生成的个性化预警建议
        advice = analyzeResponse.data.alert_message
        console.log('使用大模型生成的预警建议:', advice)
      } else {
        // 生成本地建议文本
        advice = '根据您最近三天的血糖记录分析：\n\n'
        
        if (mean > 7.8) {
          advice += '您的平均血糖偏高，建议控制碳水化合物摄入，增加运动量。\n\n'
        } else if (mean < 3.9) {
          advice += '您的平均血糖偏低，请注意及时补充碳水化合物，避免低血糖发生。\n\n'
        } else {
          advice += '您的平均血糖处于正常范围，请继续保持良好的生活方式。\n\n'
        }
        
        if (std > 2.0) {
          advice += '您的血糖波动较大，建议规律三餐，避免暴饮暴食，监测血糖的频率可以适当增加。\n\n'
        }
        
        if (inRangePercentage < 70) {
          advice += `您的血糖达标率为${inRangePercentage.toFixed(0)}%，低于理想水平(70%)，建议咨询医生调整治疗方案。\n\n`;
        } else if (riskLevel === 'normal') {
          advice = '您的血糖控制良好，各项指标均在理想范围内。请继续保持当前的健康生活方式，定期监测，预防风险。'
        } else {
          advice += '请记住，良好的饮食习惯、适当的运动和按时服药是控制血糖的关键。'
        }
      }
      
      // 更新分析数据
      glucoseAnalysis.value = {
        statistics: {
          average: mean,
          max: stats.max_value || 0,
          min: stats.min_value || 0,
          std: std,
          in_range_percentage: inRangePercentage,
          high_percentage: highPercentage,
          low_percentage: lowPercentage
        },
        patterns: {
          fasting_avg: records.filter(r => 
            ['BEFORE_BREAKFAST', 'BEFORE_LUNCH', 'BEFORE_DINNER'].includes(r.measurement_time)
          ).reduce((sum, r) => sum + r.value, 0) / 
          Math.max(1, records.filter(r => 
            ['BEFORE_BREAKFAST', 'BEFORE_LUNCH', 'BEFORE_DINNER'].includes(r.measurement_time)
          ).length),
          postprandial_avg: records.filter(r => 
            ['AFTER_BREAKFAST', 'AFTER_LUNCH', 'AFTER_DINNER'].includes(r.measurement_time)
          ).reduce((sum, r) => sum + r.value, 0) / 
          Math.max(1, records.filter(r => 
            ['AFTER_BREAKFAST', 'AFTER_LUNCH', 'AFTER_DINNER'].includes(r.measurement_time)
          ).length)
        },
        advice: advice,
        risk_level: riskLevel, // 设置风险等级
        record_count: records.length,
        updated_at: new Date().toISOString()
      }
      
      hasAnalysisData.value = true
    } else {
      hasAnalysisData.value = false
      ElMessage.info('暂无足够的血糖数据进行分析')
    }
  } catch (error) {
    console.error('获取血糖分析失败:', error)
    ElMessage.error('获取血糖分析失败，请稍后再试')
    hasAnalysisData.value = false
  } finally {
    loadingAnalysis.value = false
  }
}

// 获取饮食建议
const fetchDietSuggestions = async () => {
  if (!hasGlucoseData.value) {
    ElMessage.warning('需要血糖数据才能生成饮食建议')
    return
  }
  
  try {
    loadingDietSuggestions.value = true
    
    // 暂时移除大模型API调用，直接使用模拟数据
    // const latestGlucose = glucoseRecords.value[0]?.value || 0
    // const isMealTime = new Date().getHours() >= 6 && new Date().getHours() <= 20
    // const isBeforeMeal = isMealTime && Math.random() > 0.5
    
    // 不再调用API，直接使用模拟数据
    // const response = await apiClient.get('/api/v1/glucose-monitor/quick-diet-suggestions', {
    //   params: {
    //     glucose_value: latestGlucose,
    //     meal_type: selectedMealType.value,
    //     is_before_meal: isBeforeMeal
    //   }
    // })
    
    // 直接使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 500)) // 模拟延迟
    simulateDietSuggestions()
    
  } catch (error) {
    console.error('获取饮食建议失败:', error)
    // 出错时也使用模拟数据
    simulateDietSuggestions()
  } finally {
    loadingDietSuggestions.value = false
  }
}

// 模拟饮食建议数据（在API未实现时使用）
const simulateDietSuggestions = () => {
  const latestGlucose = glucoseRecords.value[0]?.value || 7.2
  const isBeforeMeal = Math.random() > 0.5
  const status = getGlucoseStatus(latestGlucose, isBeforeMeal)
  
  let suggestion = ''
  let recommended: string[] = []
  let avoid: string[] = []
  let mealPlan = ''
  
  if (status === 'high') {
    suggestion = '您的血糖偏高，建议减少碳水化合物摄入，增加蛋白质和膳食纤维。'
    recommended = ['蔬菜沙拉', '鸡胸肉', '豆腐', '牛油果', '坚果少量']
    avoid = ['白米饭', '白面包', '甜点', '含糖饮料']
    mealPlan = '推荐：烤鸡胸肉100g + 混合蔬菜沙拉 + 藜麦50g'
  } else if (status === 'low') {
    suggestion = '您的血糖偏低，建议适量摄入优质碳水化合物，避免空腹过久。'
    recommended = ['全麦面包', '燕麦', '香蕉', '酸奶', '蜂蜜少量']
    avoid = ['精制糖', '果汁', '咖啡因饮料']
    mealPlan = '推荐：全麦面包2片 + 煮鸡蛋1个 + 小香蕉1根'
  } else {
    suggestion = '您的血糖正常，建议保持均衡饮食，控制碳水化合物摄入量。'
    recommended = ['全谷物', '绿叶蔬菜', '鱼肉', '豆制品', '坚果适量']
    avoid = ['精制碳水', '甜点', '油炸食品']
    mealPlan = '推荐：糙米饭半碗 + 清蒸鱼100g + 西兰花 + 豆腐'
  }
  
  dietSuggestions.value = {
    current_status: `您的当前血糖为${latestGlucose.toFixed(1)} mmol/L，属于${isBeforeMeal ? '餐前' : '餐后'}${status === 'normal' ? '正常' : status === 'high' ? '偏高' : '偏低'}范围。`,
    glucose_status: status,
    quick_suggestion: suggestion,
    recommended_foods: recommended,
    foods_to_avoid: avoid,
    meal_plan_example: mealPlan
  }
  
  hasDietSuggestions.value = true
}

// 根据血糖值判断状态
const getGlucoseStatus = (value: number, isBeforeMeal: boolean): 'high' | 'normal' | 'low' => {
  if (isBeforeMeal) {
    if (value < 3.9) return 'low'
    if (value > 7.0) return 'high'
    return 'normal'
  } else {
    if (value < 3.9) return 'low'
    if (value > 10.0) return 'high'
    return 'normal'
  }
}

// 获取饮食状态对应的CSS类
const getDietStatusClass = (status: string) => {
  if (status === 'high') return 'status-high'
  if (status === 'low') return 'status-low'
  return 'status-normal'
}

// 刷新饮食建议
const refreshDietSuggestions = () => {
  fetchDietSuggestions()
}

// 更新餐食建议
const updateMealSuggestion = async () => {
  try {
    loadingDietSuggestions.value = true
    
    // 在实际应用中，这里应该调用API获取特定餐食类型的建议
    // 这里使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const mealPlans = {
      breakfast: '早餐推荐：全麦面包2片 + 煮鸡蛋1个 + 牛奶200ml',
      lunch: '午餐推荐：糙米饭半碗 + 清蒸鱼100g + 西兰花 + 豆腐',
      dinner: '晚餐推荐：藜麦沙拉 + 烤鸡胸肉100g + 烤红薯小份',
      snack: '加餐推荐：无糖酸奶100g + 蓝莓一小把或坚果10g'
    }
    
    dietSuggestions.value.meal_plan_example = mealPlans[selectedMealType.value]
  } catch (error) {
    console.error('更新餐食建议失败:', error)
  } finally {
    loadingDietSuggestions.value = false
  }
}

// 显示详细饮食建议
const showDetailedDietSuggestions = async () => {
  try {
    ElMessage.info('正在生成详细饮食建议...')
    
    const response = await apiClient.post('/api/v1/glucose-monitor/analyze-trend', { days: 3 }, {
      timeout: 30000 
    })
    
    if (!response.data || !response.data.advice) {
      throw new Error('无法获取血糖分析和建议')
    }
    
    const adviceContent = response.data.advice
    
    let processedAdvice = adviceContent
      .replace(/\n\n/g, '<br><br>')
      .replace(/###\s+(.*?)(\n|$)/g, '<h3>$1</h3>')
      .replace(/####\s+(.*?)(\n|$)/g, '<h4>$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    
    detailedAdviceContent.value = `
      <div class="blood-glucose-analysis">
        ${processedAdvice}
      </div>
      <h4 class="additional-meal-suggestions">根据您选择的餐型，我们提供以下建议</h4>
      <p><strong>${selectedMealType.value === 'breakfast' ? '早餐' : 
                    selectedMealType.value === 'lunch' ? '午餐' : 
                    selectedMealType.value === 'dinner' ? '晚餐' : '加餐'}</strong>：
         <span style="color:#409EFF">${dietSuggestions.value.meal_plan_example}</span>
      </p>
    `
    showDetailedAdviceCard.value = true
  } catch (error) {
    console.error('获取详细饮食建议失败:', error)
    ElMessage.error('获取详细饮食建议失败，请稍后再试')
    
    fallbackToLocalSuggestions()
  }
}

// 回退到本地静态建议
const fallbackToLocalSuggestions = () => {
  const detailedSuggestion = `
    <h3>个性化饮食建议</h3>
    <p>基于您的血糖数据分析，我们为您提供以下饮食建议：</p>
    
    <h4>总体原则</h4>
    <ul>
      <li>控制碳水化合物总量，选择低GI值的碳水食物</li>
      <li>增加蛋白质和健康脂肪的摄入</li>
      <li>多吃富含膳食纤维的蔬菜</li>
      <li>规律三餐，避免长时间空腹</li>
    </ul>
    
    <h4>推荐食物清单</h4>
    <ul>
      <li><strong>碳水来源</strong>：全麦面包、燕麦、糙米、藜麦、红薯</li>
      <li><strong>蛋白质来源</strong>：鸡胸肉、鱼、豆腐、鸡蛋、希腊酸奶</li>
      <li><strong>健康脂肪</strong>：牛油果、橄榄油、坚果(适量)</li>
      <li><strong>蔬菜水果</strong>：西兰花、菠菜、芦笋、蓝莓、草莓(适量)</li>
    </ul>
    
    <h4>一日三餐建议</h4>
    <p><strong>早餐</strong>：${selectedMealType.value === 'breakfast' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '全麦面包2片 + 煮鸡蛋1个 + 牛奶200ml'}</p>
    <p><strong>午餐</strong>：${selectedMealType.value === 'lunch' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '糙米饭半碗 + 清蒸鱼100g + 西兰花 + 豆腐'}</p>
    <p><strong>晚餐</strong>：${selectedMealType.value === 'dinner' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '藜麦沙拉 + 烤鸡胸肉100g + 烤红薯小份'}</p>
    <p><strong>加餐</strong>：${selectedMealType.value === 'snack' ? '<span style="color:#409EFF">'+dietSuggestions.value.meal_plan_example+'</span>' : '无糖酸奶100g + 蓝莓一小把或坚果10g'}</p>
  `
  detailedAdviceContent.value = detailedSuggestion
  showDetailedAdviceCard.value = true
}

// 辅助方法：根据血糖值获取CSS类
const getValueClass = (value) => {
  if (value > 10.0) return 'high-value'
  if (value < 3.9) return 'low-value'
  return 'normal-value'
}

// 辅助方法：根据达标率获取CSS类
const getRangeClass = (percentage) => {
  if (percentage >= 70) return 'good-range'
  if (percentage >= 50) return 'average-range'
  return 'poor-range'
}

// 辅助方法：根据标准差获取CSS类
const getStdClass = (std) => {
  if (std <= 1.5) return 'stable-std'
  if (std <= 2.5) return 'moderate-std'
  return 'unstable-std'
}

// 辅助方法：根据标准差获取波动性描述
const getVariabilityText = (std) => {
  if (std <= 1.5) return '稳定'
  if (std <= 2.5) return '一般'
  return '波动大'
}

// 截断建议文本，显示预览
const truncateAdvice = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 显示完整建议
const showFullAdvice = async () => {
  try {
    // 显示加载提示
    ElMessage.info('正在获取最新的血糖风险评估...')
    
    // 首先调用analyze接口获取预警信息
    const alertResponse = await apiClient.post('/api/v1/glucose-monitor/analyze', {
      hours: 72 // 分析最近72小时的数据
    }, {
      timeout: 30000 // 设置30秒超时时间
    })
    
    // 然后调用analyze-trend接口获取详细的血糖分析报告
    const trendResponse = await apiClient.post('/api/v1/glucose-monitor/analyze-trend', { 
      days: 3 
    }, {
      timeout: 30000 // 设置30秒超时时间
    })
    
    if (!trendResponse.data || !trendResponse.data.advice) {
      throw new Error('无法获取血糖分析和建议')
    }
    
    // 使用大模型生成的血糖分析报告和建议
    const adviceContent = trendResponse.data.advice
    let dialogTitle = '血糖风险评估与管理建议'
    
    // 更新当前的建议内容
    glucoseAnalysis.value.advice = adviceContent
    
    // 如果有预警信息，添加到顶部警报区域
    if (alertResponse.data?.has_alerts && alertResponse.data?.alert_message) {
      // 清除现有的相似警报
      glucoseAlerts.value = glucoseAlerts.value.filter(alert => !alert.title.includes('血糖异常'))
      
      // 添加新的警报，显示大模型生成的个性化预警信息
      addAlert(
        '血糖异常预警', 
        alertResponse.data.alert_message, 
        alertResponse.data.alerts.some(a => a.severity === 'high') ? 'error' : 'warning'
      )
    }
    
    // 将大模型生成的文本处理为HTML格式
    let processedAdvice = adviceContent
      .replace(/\n\n/g, '<br><br>') // 替换双换行为HTML换行
      .replace(/###\s+(.*?)(\n|$)/g, '<h3>$1</h3>') // 处理 ### 标题
      .replace(/####\s+(.*?)(\n|$)/g, '<h4>$1</h4>') // 处理 #### 标题
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // 处理加粗文本
    
    // 如果有预警信息，在分析报告前添加预警信息
    let contentToShow = ``
    
    if (alertResponse.data?.has_alerts && alertResponse.data?.alert_message) {
      contentToShow = `
        <div class="glucose-alert-warning">
          <h3>⚠️ 血糖异常预警</h3>
          <p>${alertResponse.data.alert_message}</p>
        </div>
        <div class="blood-glucose-analysis ai-analysis-content">
          ${processedAdvice}
        </div>
      `
    } else {
      contentToShow = `
        <div class="blood-glucose-analysis ai-analysis-content">
          ${processedAdvice}
        </div>
      `
    }
    
    // ! 移除 ElMessageBox.alert，改为显示自定义模态框
    fullAnalysisContent.value = contentToShow
    showFullAnalysisCard.value = true
    
  } catch (error) {
    console.error('获取血糖风险评估失败:', error)
    ElMessage.error('获取血糖风险评估失败，请稍后再试')
    
    // 错误时回退到本地静态建议，并显示在新的模态框中
    const staticAdvice = `
      <h3>血糖管理建议</h3>
      <p>很抱歉，无法获取实时血糖分析。以下是基于通用规则的建议：</p>
      
      <h4>血糖管理原则</h4>
      <ul>
        <li>保持规律饮食，避免暴饮暴食</li>
        <li>增加体育活动，每天至少30分钟中等强度运动</li>
        <li>按时服药，遵医嘱调整药物剂量</li>
        <li>定期监测血糖，记录变化趋势</li>
        <li>避免过度疲劳和精神压力</li>
      </ul>
      
      <h4>监测提示</h4>
      <p>建议继续监测并记录您的血糖值，特别是在餐前和餐后2小时的数值，这将有助于更准确地评估您的血糖控制情况。</p>
    `
    
    fullAnalysisContent.value = `<div class="blood-glucose-analysis ai-analysis-content">${staticAdvice}</div>`
    showFullAnalysisCard.value = true
  }
}

// 同步设备数据
const syncDevice = async () => {
  try {
    ElMessage.info('开始同步设备数据...')
    
    // 直接刷新血糖数据，不调用不存在的同步API
    const result = await fetchGlucoseData()
    
    if (result && result.success) {
      ElMessage.success('设备数据同步成功')
      
      // 分析血糖数据
      await analyzeGlucoseData()
      
      // 获取三天分析
      await fetchGlucoseAnalysis()
      
      // 重新初始化图表
      if (hasGlucoseData.value) {
        chartKey.value++ // 强制重新渲染
        await nextTick()
        initGlucoseChart()
      }
    } else {
      ElMessage.warning('设备数据同步失败')
    }
  } catch (error) {
    console.error('同步设备数据失败:', error)
    ElMessage.error('同步设备数据失败，请检查设备连接')
  }
}
</script>

<style scoped>
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 定义主题色变量 */
:root {
  --metric-color: #2ecc71; /* 绿色 */
  --diet-suggestion-color: #e67e22; /* 橙色 */
  --diet-record-color: #f1c40f; /* 黄色 */
  --glucose-monitor-color: #3498db; /* 蓝色 */
  --reminder-color: #9b59b6; /* 紫色 */
  --knowledge-color: #34495e; /* 深蓝灰色 */
}

.dashboard-container {
  --dash-bg: #eef2f7;
  --dash-surface: #ffffff;
  --dash-border: #e8edf3;
  --dash-text: #1f2a37;
  --dash-muted: #6b7280;
  --dash-accent: #3b82f6;
  --dash-radius: 12px;
  --dash-gap: 10px;

  width: 100%;
  max-width: none;
  min-height: 100%;
  margin: 0;
  padding: 0 0 12px;
  background: transparent;
  color: var(--dash-text);
  font-family: 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  box-sizing: border-box;
}

.dashboard-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 300px);
  gap: 10px;
  align-items: start;
  width: 100%;
}

.dashboard-container--dense {
  --dash-gap: 8px;
}

.dashboard-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--dash-gap);
}

.dashboard-aside {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--dash-gap);
  position: sticky;
  top: 0;
}

.welcome-panel--dense {
  margin-bottom: 8px;
  padding: 10px 14px;
}

.welcome-panel--dense h2 {
  font-size: 18px;
}

.welcome-panel--dense .welcome-sub {
  margin-top: 2px;
  font-size: 12px;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  border: 1px solid var(--dash-border);
  border-radius: var(--dash-radius);
  background: #fff;
}

.metric-strip-item {
  min-width: 0;
  padding: 2px 4px;
}

.metric-strip-item span {
  display: block;
  color: var(--dash-muted);
  font-size: 11px;
  margin-bottom: 2px;
}

.metric-strip-item strong {
  display: block;
  color: var(--dash-text);
  font-size: 14px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-strip-item small {
  color: var(--dash-muted);
  font-size: 11px;
  font-weight: 500;
}

.metric-strip-more {
  justify-self: end;
  white-space: nowrap;
}

.entry-rail {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.entry-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--dash-border);
  border-radius: 12px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 1px 1px rgba(16, 24, 40, 0.02);
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.entry-chip:hover {
  border-color: #c7d2fe;
  background: #f8faff;
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.06);
}

.entry-chip strong {
  font-size: 13px;
  color: var(--dash-text);
}

.entry-chip span {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: var(--dash-muted);
  font-size: 11px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collapse-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 12px;
  border: 1px solid var(--dash-border);
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.collapse-row:hover {
  border-color: #dbe4ff;
  background: #fafbff;
}

.collapse-row-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.collapse-row-main strong {
  font-size: 13px;
  color: var(--dash-text);
}

.reminder-panel {
  margin-top: -2px;
  padding: 4px 10px 8px;
  border: 1px solid var(--dash-border);
  border-top: 0;
  border-radius: 0 0 10px 10px;
  background: #fff;
}

.reminder-panel .reminder-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.reminder-panel .reminder-item:last-child {
  border-bottom: 0;
}

.quick-nav {
  padding: 10px;
  border: 1px solid var(--dash-border);
  border-radius: 12px;
  background: #fff;
}

.quick-nav-label {
  margin-bottom: 8px;
  color: var(--dash-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.quick-nav-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.quick-nav-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #e8edf5;
  border-radius: 999px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}

.quick-nav-item .el-icon {
  flex-shrink: 0;
  font-size: 14px;
  color: #64748b;
}

.quick-nav-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-nav-item:hover {
  border-color: #c7d2fe;
  background: #eef2ff;
  color: #3730a3;
  box-shadow: 0 1px 2px rgba(79, 70, 229, 0.08);
}

.quick-nav-item:hover .el-icon {
  color: #4f46e5;
}

.quick-nav-item--accent {
  border-color: #ddd6fe;
  background: linear-gradient(180deg, #f5f3ff 0%, #eef2ff 100%);
  color: #4338ca;
}

.quick-nav-item--accent .el-icon {
  color: #4f46e5;
}

.quick-nav-item--accent:hover {
  border-color: #a5b4fc;
  background: #e0e7ff;
}

/* 问助理占满第二行右侧时更醒目：5 项里最后一项跨列可选，默认两列网格即可 */
.quick-nav-list .quick-nav-item--accent {
  grid-column: 1 / -1;
  justify-content: center;
}

.chart-card--dense :deep(.el-card__header) {
  padding: 8px 10px;
}

.chart-card--dense :deep(.el-card__body) {
  padding: 8px 10px 10px;
}

.chart-container--dense {
  min-height: 160px !important;
  height: clamp(150px, 22vh, 240px) !important;
}

.chart-container--dense .chart {
  min-height: 150px !important;
}

.glucose-drawer {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.drawer-hint {
  margin: 0;
  color: var(--dash-muted);
  font-size: 13px;
  line-height: 1.5;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.dashboard-container :deep(.el-card) {
  margin-bottom: 0;
  width: 100%;
  border: 1px solid var(--dash-border);
  border-radius: var(--dash-radius);
  background: var(--dash-surface);
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
  overflow: hidden;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.dashboard-container :deep(.el-card:hover) {
  border-color: #d7e0ea;
  box-shadow: 0 6px 16px rgba(16, 24, 40, 0.06);
  transform: none;
}

.dashboard-container :deep(.el-card__header) {
  padding: 12px 14px 10px;
  border-bottom: 1px solid #f0f3f7;
}

.dashboard-container :deep(.el-card__body) {
  padding: 12px 14px 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 15px;
  color: var(--dash-text);
  border-bottom: none;
  padding-bottom: 0;
}

.card-title-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.card-title-block small {
  color: var(--dash-muted);
  font-size: 12px;
  font-weight: 400;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 轻量色条，避免彩虹左边框抢视线 */
.metric-card { border-top: 3px solid #10b981; }
.diet-suggestion-card { border-top: 3px solid #f59e0b; }
.diet-card { border-top: 3px solid #eab308; }
.glucose-card { border-top: 3px solid #3b82f6; }
.reminder-card { border-top: 3px solid #8b5cf6; }
.knowledge-card { border-top: 3px solid #64748b; }

.panel-card {
  height: 100%;
}

.welcome-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  margin-bottom: 14px;
  padding: 14px 18px;
  border: 1px solid #dbe4ff;
  border-radius: var(--dash-radius);
  background:
    radial-gradient(circle at top right, rgba(99, 102, 241, 0.14), transparent 42%),
    linear-gradient(135deg, #4f46e5 0%, #6366f1 48%, #7c3aed 100%);
  color: #fff;
  box-shadow: 0 8px 18px rgba(79, 70, 229, 0.14);
  box-sizing: border-box;
}

.welcome-copy {
  min-width: 0;
}

.welcome-kicker {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.8;
}

.welcome-panel h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 650;
  line-height: 1.25;
  color: #fff;
}

.welcome-sub {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.88;
}

.welcome-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.welcome-actions :deep(.el-button.is-plain),
.welcome-actions :deep(.el-button--primary.is-plain) {
  --el-button-bg-color: rgba(255, 255, 255, 0.14);
  --el-button-text-color: #fff;
  --el-button-border-color: rgba(255, 255, 255, 0.35);
  --el-button-hover-bg-color: rgba(255, 255, 255, 0.22);
  --el-button-hover-text-color: #fff;
  --el-button-hover-border-color: rgba(255, 255, 255, 0.55);
}

.welcome-actions :deep(.el-button.is-text) {
  color: rgba(255, 255, 255, 0.92);
}

.compact-empty {
  padding: 8px 0 4px;
}

.compact-empty :deep(.el-empty__description) {
  margin-top: 8px;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.compact-form :deep(.el-form-item__label) {
  margin-bottom: 4px !important;
  line-height: 1.2;
  color: var(--dash-muted);
}

.welcome-actions .button {
  --white: #ffe7ff;
  --purple-100: #f4b1fd;
  --purple-200: #d190ff;
  --purple-300: #c389f2;
  --purple-400: #8e26e2;
  --purple-500: #5e2b83;
  --radius: 12px;

  border-radius: var(--radius);
  outline: none;
  cursor: pointer;
  font-size: 20px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background: transparent;
  letter-spacing: -1px;
  border: 0;
  position: relative;
  width: 160px;
  height: 60px;
  transform: rotate(353deg) skewX(4deg);
}

.welcome-actions .bg {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  filter: blur(1px);
}
.welcome-actions .bg::before,
.welcome-actions .bg::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: calc(var(--radius) * 1.1);
  background: var(--purple-500);
}
.welcome-actions .bg::before {
  filter: blur(5px);
  transition: all 0.3s ease;
  box-shadow:
    -7px 6px 0 0 rgb(115 75 155 / 40%),
    -14px 12px 0 0 rgb(115 75 155 / 30%),
    -21px 18px 4px 0 rgb(115 75 155 / 25%),
    -28px 24px 8px 0 rgb(115 75 155 / 15%),
    -35px 30px 12px 0 rgb(115 75 155 / 12%),
    -42px 36px 16px 0 rgb(115 75 155 / 8%),
    -56px 42px 20px 0 rgb(115 75 155 / 5%);
}

.welcome-actions .wrap {
  border-radius: inherit;
  overflow: hidden;
  height: 100%;
  transform: translate(6px, -6px);
  padding: 3px;
  background: linear-gradient(
    to bottom,
    var(--purple-100) 0%,
    var(--purple-400) 100%
  );
  position: relative;
  transition: all 0.3s ease;
}

.welcome-actions .outline {
  position: absolute;
  overflow: hidden;
  inset: 0;
  opacity: 0;
  outline: none;
  border-radius: inherit;
  transition: all 0.4s ease;
}
.welcome-actions .outline::before {
  content: "";
  position: absolute;
  inset: 2px;
  width: 120px;
  height: 300px;
  margin: auto;
  background: linear-gradient(
    to right,
    transparent 0%,
    white 50%,
    transparent 100%
  );
  animation: spin 3s linear infinite;
  animation-play-state: paused;
}

.welcome-actions .content {
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  position: relative;
  height: 100%;
  gap: 16px;
  border-radius: calc(var(--radius) * 0.85);
  font-weight: 600;
  transition: all 0.3s ease;
  background: linear-gradient(
    to bottom,
    var(--purple-300) 0%,
    var(--purple-400) 100%
  );
  box-shadow:
    inset -2px 12px 11px -5px var(--purple-200),
    inset 1px -3px 11px 0px rgb(0 0 0 / 35%);
}
.welcome-actions .content::before {
  content: "";
  inset: 0;
  position: absolute;
  z-index: 10;
  width: 80%;
  top: 45%;
  bottom: 35%;
  opacity: 0.7;
  margin: auto;
  background: linear-gradient(to bottom, transparent, var(--purple-400));
  filter: brightness(1.3) blur(5px);
}

.welcome-actions .char {
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.welcome-actions .char span {
  display: block;
  color: transparent;
  position: relative;
}
.welcome-actions .char span:nth-child(5) {
  margin-left: 5px;
}
.welcome-actions .char.state-1 span:nth-child(5) {
  margin-right: -3px;
}
.welcome-actions .char.state-1 span {
  animation: charAppear 1.2s ease backwards calc(var(--i) * 0.03s);
}
.welcome-actions .char.state-1 span::before,
.welcome-actions .char span::after {
  content: attr(data-label);
  position: absolute;
  color: var(--white);
  text-shadow: -1px 1px 2px var(--purple-500);
  left: 0;
}
.welcome-actions .char span::before {
  opacity: 0;
  transform: translateY(-100%);
}
.welcome-actions .char.state-2 {
  position: absolute;
  left: 80px;
}
.welcome-actions .char.state-2 span::after {
  opacity: 1;
}

.welcome-actions .icon {
  animation: resetArrow 0.8s cubic-bezier(0.7, -0.5, 0.3, 1.2) forwards;
  z-index: 10;
}
.welcome-actions .icon div,
.welcome-actions .icon div::before,
.welcome-actions .icon div::after {
  height: 3px;
  border-radius: 1px;
  background-color: var(--white);
}
.welcome-actions .icon div::before,
.welcome-actions .icon div::after {
  content: "";
  position: absolute;
  right: 0;
  transform-origin: center right;
  width: 14px;
  border-radius: 15px;
  transition: all 0.3s ease;
}
.welcome-actions .icon div {
  position: relative;
  width: 24px;
  box-shadow: -2px 2px 5px var(--purple-400);
  transform: scale(0.9);
  background: linear-gradient(to bottom, var(--white), var(--purple-100));
  animation: swingArrow 1s ease-in-out infinite;
  animation-play-state: paused;
}
.welcome-actions .icon div::before {
  transform: rotate(44deg);
  top: 1px;
  box-shadow: 1px -2px 3px -1px var(--purple-400);
  animation: rotateArrowLine 1s linear infinite;
  animation-play-state: paused;
}
.welcome-actions .icon div::after {
  bottom: 1px;
  transform: rotate(316deg);
  box-shadow: -2px 2px 3px 0 var(--purple-400);
  background: linear-gradient(200deg, var(--white), var(--purple-100));
  animation: rotateArrowLine2 1s linear infinite;
  animation-play-state: paused;
}

.welcome-actions .path {
  position: absolute;
  z-index: 12;
  bottom: 0;
  left: 0;
  right: 0;
  stroke-dasharray: 150 480;
  stroke-dashoffset: 150;
  pointer-events: none;
}

.welcome-actions .splash {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  stroke-dasharray: 60 60;
  stroke-dashoffset: 60;
  transform: translate(-17%, -31%);
  stroke: var(--purple-300);
}

/** STATES */

.welcome-actions .button:hover .words {
  opacity: 1;
}
.welcome-actions .button:hover .words span {
  animation-play-state: running;
}

.welcome-actions .button:hover .char.state-1 span::before {
  animation: charAppear 0.7s ease calc(var(--i) * 0.03s);
}

.welcome-actions .button:hover .char.state-1 span::after {
  opacity: 1;
  animation: charDisappear 0.7s ease calc(var(--i) * 0.03s);
}

.welcome-actions .button:hover .wrap {
  transform: translate(8px, -8px);
}

.welcome-actions .button:hover .outline {
  opacity: 1;
}

.welcome-actions .button:hover .outline::before,
.welcome-actions .button:hover .icon div::before,
.welcome-actions .button:hover .icon div::after,
.welcome-actions .button:hover .icon div {
  animation-play-state: running;
}

.welcome-actions .button:active .bg::before {
  filter: blur(5px);
  opacity: 0.7;
  box-shadow:
    -7px 6px 0 0 rgb(115 75 155 / 40%),
    -14px 12px 0 0 rgb(115 75 155 / 25%),
    -21px 18px 4px 0 rgb(115 75 155 / 15%);
}
.welcome-actions .button:active .content {
  box-shadow:
    inset -1px 12px 8px -5px rgba(71, 0, 137, 0.4),
    inset 0px -3px 8px 0px var(--purple-200);
}

.welcome-actions .button:active .words,
.welcome-actions .button:active .outline {
  opacity: 0;
}

.welcome-actions .button:active .wrap {
  transform: translate(3px, -3px);
}

.welcome-actions .button:active .splash {
  animation: splash 0.8s cubic-bezier(0.3, 0, 0, 1) forwards 0.05s;
}

.welcome-actions .button:focus .path {
  animation: path 1.6s ease forwards 0.2s;
}

.welcome-actions .button:focus .icon {
  animation: arrow 1s cubic-bezier(0.7, -0.5, 0.3, 1.5) forwards;
}

.welcome-actions .char.state-2 span::after,
.welcome-actions .button:focus .char.state-1 span {
  animation: charDisappear 0.5s ease forwards calc(var(--i) * 0.03s);
}

.welcome-actions .button:focus .char.state-2 span::after {
  animation: charAppear 1s ease backwards calc(var(--i) * 0.03s);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes charAppear {
  0% {
    transform: translateY(50%);
    opacity: 0;
    filter: blur(20px);
  }
  20% {
    transform: translateY(70%);
    opacity: 1;
  }
  50% {
    transform: translateY(-15%);
    opacity: 1;
    filter: blur(0);
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes charDisappear {
  0% {
    transform: translateY(0);
    opacity: 1;
  }
  100% {
    transform: translateY(-70%);
    opacity: 0;
    filter: blur(3px);
  }
}

@keyframes arrow {
  0% {
    opacity: 1;
  }
  50% {
    transform: translateX(60px);
    opacity: 0;
  }
  51% {
    transform: translateX(-200px);
    opacity: 0;
  }
  100% {
    transform: translateX(-128px);
    opacity: 1;
  }
}

@keyframes swingArrow {
  50% {
    transform: translateX(5px) scale(0.9);
  }
}

@keyframes rotateArrowLine {
  50% {
    transform: rotate(30deg);
  }
  80% {
    transform: rotate(55deg);
  }
}

@keyframes rotateArrowLine2 {
  50% {
    transform: rotate(330deg);
  }
  80% {
    transform: rotate(300deg);
  }
}

@keyframes resetArrow {
  0% {
    transform: translateX(-128px);
  }
  100% {
    transform: translateX(0);
  }
}

@keyframes path {
  from {
    stroke: white;
  }
  to {
    stroke-dashoffset: -480;
    stroke: #f9c6fe;
  }
}

@keyframes splash {
  to {
    stroke-dasharray: 2 60;
    stroke-dashoffset: -60;
  }
}

.chart-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: auto;
  padding: 0;
  opacity: 1;
  animation: none;
}

.chart-card.is-empty {
  min-height: 0;
}

.chart-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-loading,
.chart-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 88px;
  padding: 4px 0 8px;
}

.inline-empty {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px 14px;
  width: 100%;
  padding: 8px;
  text-align: center;
}

.inline-empty p {
  margin: 0;
  color: var(--dash-muted);
  font-size: 13px;
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 220px;
  height: clamp(200px, 28vh, 320px);
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.metrics-container {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.metric-item {
  text-align: left;
  padding: 12px 14px;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 12px;
}

.metric-label {
  color: var(--dash-muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--dash-text);
  line-height: 1.2;
}

.metric-value small {
  margin-left: 2px;
  color: var(--dash-muted);
  font-size: 12px;
  font-weight: 500;
}

.diet-card .diet-list {
  padding: 0 10px;
}

.diet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eef2f7;
}

.diet-item:last-child {
  border-bottom: none;
}

.diet-time {
  font-size: 0.9rem;
  color: #576b81;
  width: 30%;
  font-weight: 500;
}

.diet-name {
  flex: 1;
  font-weight: 500;
}

.diet-calories {
  color: var(--diet-record-color);
  font-weight: 600;
}

.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reminder-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 10px;
  transition: background-color 0.3s;
}

.reminder-icon {
  margin-right: 12px;
  font-size: 1.4rem;
  color: var(--reminder-color);
}

.reminder-icon.done {
  color: #2ecc71;
}

.reminder-content {
  flex: 1;
}

.reminder-text {
  font-weight: 600;
  color: #2c3e50;
}

.reminder-time {
  font-size: 0.8rem;
  color: #576b81;
}

.reminder-item .el-checkbox {
  margin-left: 10px;
}

.knowledge-item {
  padding: 16px 0;
  border-bottom: 1px solid #eef2f7;
}

.knowledge-item:last-child {
  border-bottom: none;
}

.knowledge-title {
  font-weight: 600;
  margin-bottom: 6px;
  color: #2c3e50;
}

.knowledge-desc {
  font-size: 0.9rem;
  color: #576b81;
  margin-bottom: 12px;
}

.knowledge-item .el-button {
  font-weight: 600;
}

.card-footer {
  margin-top: 16px;
  text-align: center;
}

.empty-data {
  padding: 40px 0;
}

.loading-container {
  padding: 20px;
}

.glucose-card .card-header {
  border-bottom: none;
}

.quick-import {
  padding: 10px 5px;
}

.quick-import h4 {
  margin-bottom: 15px;
  color: var(--glucose-monitor-color);
  font-weight: 600;
}

.quick-import .el-button {
  border-radius: 8px;
  font-weight: 600;
}

.glucose-alerts {
  margin-bottom: 15px;
}

.glucose-alerts .el-alert {
  margin-bottom: 10px;
  border-radius: 8px;
}

.glucose-alerts .el-alert:last-child {
  margin-bottom: 0;
}

/* 智能分析相关样式 */
.glucose-analysis {
  margin-top: 10px;
}

.analysis-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.summary-item {
  text-align: center;
  flex: 1;
  padding: 12px 0;
  border-radius: 12px;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 13px;
  font-weight: 500;
}

.normal-value { background-color: rgba(46, 204, 113, 0.1); color: #2ecc71; }
.high-value { background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; }
.low-value { background-color: rgba(243, 156, 18, 0.1); color: #f39c12; }

.good-range { background-color: rgba(46, 204, 113, 0.1); color: #2ecc71; }
.average-range { background-color: rgba(243, 156, 18, 0.1); color: #f39c12; }
.poor-range { background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; }

.stable-std { background-color: rgba(46, 204, 113, 0.1); color: #2ecc71; }
.moderate-std { background-color: rgba(243, 156, 18, 0.1); color: #f39c12; }
.unstable-std { background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; }

.advice-preview {
  background-color: #eaf5ff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 10px;
  border: 1px solid #a8d8ff;
}

.advice-title {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: var(--glucose-monitor-color);
  font-weight: 600;
}

.advice-title .el-icon {
  margin-right: 8px;
  font-size: 1.2rem;
}

.advice-content {
  font-size: 14px;
  line-height: 1.6;
  color: #34495e;
  margin-bottom: 8px;
}

.empty-analysis {
  padding: 15px 0;
  text-align: center;
}

/* 对话框样式 */
:deep(.advice-dialog .el-message-box__content) {
  max-height: 400px;
  overflow-y: auto;
}

.diet-suggestion-card .card-header {
  border-bottom: none;
}

.diet-status-banner {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 15px;
  font-size: 14px;
  font-weight: 600;
}

.diet-status-banner .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.status-normal {
  background-color: rgba(46, 204, 113, 0.15);
  color: #27ae60;
  border-left: 5px solid #2ecc71;
}

.status-high {
  background-color: rgba(231, 76, 60, 0.15);
  color: #c0392b;
  border-left: 5px solid #e74c3c;
}

.status-low {
  background-color: rgba(243, 156, 18, 0.15);
  color: #d35400;
  border-left: 5px solid #f39c12;
}

.diet-suggestion-content {
  padding: 0 5px;
}

.suggestion-text {
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
  color: #34495e;
}

.food-section {
  margin-bottom: 20px;
}

.food-section h4 {
  font-size: 15px;
  margin-bottom: 10px;
  color: #2c3e50;
  font-weight: 600;
}

.food-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.food-tag {
  border-radius: 16px;
  padding: 0 15px;
  height: 32px;
  line-height: 30px;
  font-weight: 500;
}

.next-meal {
  margin: 20px 0;
}

.meal-type-selector {
  margin-bottom: 15px;
  text-align: center;
}

.meal-suggestion {
  background-color: #f0f4f8;
  padding: 15px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: #34495e;
  text-align: center;
  border: 1px dashed #bdc3c7;
}

.card-footer {
  margin-top: 20px;
  text-align: center;
}

:deep(.diet-suggestion-dialog .el-message-box__content) {
  max-height: 400px;
  overflow-y: auto;
}

:deep(.diet-suggestion-dialog ul) {
  padding-left: 20px;
  margin: 10px 0;
  list-style-type: "✨ ";
}

:deep(.diet-suggestion-dialog h3, .diet-suggestion-dialog h4) {
  margin: 15px 0 10px 0;
  color: #0072ff;
}

:deep(.diet-suggestion-dialog .blood-glucose-analysis) {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

:deep(.diet-suggestion-dialog .additional-meal-suggestions) {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
}

:deep(.diet-suggestion-dialog strong) {
  color: #303133;
}

@media (max-width: 992px) {
  .metrics-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 15px;
  }
  .welcome-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .metrics-container, .analysis-summary {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 576px) {
  .metrics-container, .analysis-summary {
    grid-template-columns: 1fr;
  }
  .welcome-text h2 {
    font-size: 1.8rem;
  }
  .welcome-actions {
    flex-direction: column;
    width: 100%;
  }
}

/* 添加AI血糖风险评估容器样式 */
.ai-alert-container {
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 15px;
  border: 1px solid;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease-in-out;
}

.ai-alert-good {
  background-color: #f0f9eb;
  border-color: #e1f3d8;
}

.ai-alert-warning {
  background-color: #fdf6ec;
  border-color: #faecd8;
}

.ai-alert-danger {
  background-color: #fff6f6;
  border-color: #ffd6d6;
}

.ai-alert-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
}

.ai-alert-good .ai-alert-header { color: #67c23a; }
.ai-alert-warning .ai-alert-header { color: #e6a23c; }
.ai-alert-danger .ai-alert-header { color: #f56c6c; }

.ai-alert-header .el-icon {
  margin-right: 8px;
  font-size: 1.2rem;
}

.ai-alert-content {
  font-size: 14px;
  line-height: 1.6;
  color: #34495e;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #fff;
  border-radius: 8px;
  border-left: 3px solid;
}

.ai-alert-good .ai-alert-content { border-left-color: #67c23a; }
.ai-alert-warning .ai-alert-content { border-left-color: #e6a23c; }
.ai-alert-danger .ai-alert-content { border-left-color: #f56c6c; }

/* 对话框中AI分析内容的样式 */
:deep(.advice-dialog .ai-analysis-content) {
  line-height: 1.6;
  font-size: 14px;
}

:deep(.advice-dialog .ai-analysis-content h3) {
  color: #e74c3c;
  margin: 16px 0 8px 0;
  font-size: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}

:deep(.advice-dialog .ai-analysis-content h4) {
  color: #2c3e50;
  margin: 14px 0 8px 0;
  font-size: 15px;
}

:deep(.advice-dialog .ai-analysis-content strong) {
  color: #e74c3c;
  font-weight: 600;
}

:deep(.advice-dialog .el-message-box__content) {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
}

:deep(.advice-dialog .el-message-box__header) {
  background-color: #f8f9fb;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

/* 新增：血糖预警消息样式 */
:deep(.glucose-alert-warning) {
  background-color: #fff6f6;
  border: 1px solid #ffd6d6;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

:deep(.glucose-alert-warning h3) {
  color: #e74c3c;
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  display: flex;
  align-items: center;
}

:deep(.glucose-alert-warning p) {
  color: #333;
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}

/* 详细建议卡片的动画延迟 */
.detailed-advice-card {
  animation-delay: 0s;
}

.el-card:hover {
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  border-left: 5px solid var(--knowledge-color);
}

.advice-content-wrapper {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 15px; /* for scrollbar */
}

.advice-content-wrapper h3, .advice-content-wrapper h4 {
  margin: 15px 0 10px 0;
  color: #0072ff;
}
.advice-content-wrapper .blood-glucose-analysis {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}
.advice-content-wrapper .additional-meal-suggestions {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
}
.advice-content-wrapper strong {
  color: #303133;
}
.advice-content-wrapper ul {
  padding-left: 20px;
  margin: 10px 0;
  list-style-type: "✨ ";
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-card {
  width: 90%;
  max-width: 800px;
  margin: 0;
  opacity: 0;
  transform: scale(0.9);
  animation: modal-pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

@keyframes modal-pop-in {
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 新增：完整分析卡片的样式 */
.full-analysis-card {
}

.el-card:hover {
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  border-left: 5px solid var(--knowledge-color);
}

.advice-content-wrapper {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
}

.advice-content-wrapper h3, .advice-content-wrapper h4 {
  margin: 15px 0 10px 0;
  color: #0072ff;
}

.advice-content-wrapper .blood-glucose-analysis {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fb;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

.advice-content-wrapper .additional-meal-suggestions {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
}

.advice-content-wrapper strong {
  color: #303133;
}

.advice-content-wrapper ul {
  padding-left: 20px;
  margin: 10px 0;
  list-style-type: "✨ ";
}

/* 模态卡片头部的通用样式 */
.modal-card .card-header {
  background-color: #f8f9fb;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

/* 新增欢迎卡片加载器样式 */
.welcome-loader-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 160px; /* 确保加载器有足够的空间显示 */
}

.loader {
  position: relative;
  width: 240px;
  height: 130px;
  margin-bottom: 10px;
  border: 1px solid #d3d3d3;
  padding: 15px;
  background-color: #e3e3e3;
  overflow: hidden;
}

.loader:after {
  content: "";
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: linear-gradient(110deg, rgba(227, 227, 227, 0) 0%, rgba(227, 227, 227, 0) 40%, rgba(227, 227, 227, 0.5) 50%, rgba(227, 227, 227, 0) 60%, rgba(227, 227, 227, 0) 100%);
  animation: gradient-animation_2 1.2s linear infinite;
}

.loader .wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.loader .wrapper > div {
  background-color: #cacaca;
}

.loader .circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

.loader .button {
  display: inline-block;
  height: 32px;
  width: 75px;
}

.loader .line-1 {
  position: absolute;
  top: 11px;
  left: 58px;
  height: 10px;
  width: 100px;
}

.loader .line-2 {
  position: absolute;
  top: 34px;
  left: 58px;
  height: 10px;
  width: 150px;
}

.loader .line-3 {
  position: absolute;
  top: 57px;
  left: 0px;
  height: 10px;
  width: 100%;
}

.loader .line-4 {
  position: absolute;
  top: 80px;
  left: 0px;
  height: 10px;
  width: 92%;
}

@keyframes gradient-animation_2 {
  0% {
    transform: translateX(-100%);
  }

  100% {
    transform: translateX(100%);
  }
}

.diet-loader-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px; /* Ensure enough space for the animation */
}

/* Pizza animation CSS from uiverse.io/AkshatDaxini/jolly-hound-16 */
.main {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  border-radius: 12px; /* Match card border-radius */
}

#pizza {
  animation: rotate 4s linear infinite; /* Rotate the entire pizza */
  transform-origin: 82px 79.5px; /* Center of the pizza */
}

#slice6 {
  animation: slice6 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice5 {
  animation: slice5 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice4 {
  animation: slice4 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice3 {
  animation: slice3 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice2 {
  animation: slice2 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}
#slice1 {
  animation: slice1 2s ease-in-out infinite alternate;
  transform-origin: 82px 79.5px;
}

#pepperoni {
  animation: pepperoni 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_2 {
  animation: pepperoni_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_3 {
  animation: pepperoni_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_4 {
  animation: pepperoni_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_5 {
  animation: pepperoni_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepperoni_6 {
  animation: pepperoni_6 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

#mushroom {
  animation: mushroom 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_2 {
  animation: mushroom_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_3 {
  animation: mushroom_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_4 {
  animation: mushroom_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#mushroom_5 {
  animation: mushroom_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

#onion {
  animation: onion 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_2 {
  animation: onion_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_3 {
  animation: onion_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_4 {
  animation: onion_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_5 {
  animation: onion_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#onion_6 {
  animation: onion_6 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

#pepper {
  animation: pepper 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_2 {
  animation: pepper_2 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_3 {
  animation: pepper_3 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_4 {
  animation: pepper_4 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_5 {
  animation: pepper_5 2s ease-in-out infinite alternate;
  transform-origin: center center;
}
#pepper_6 {
  animation: pepper_6 2s ease-in-out infinite alternate;
  transform-origin: center center;
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes slice6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(5px, -5px);
  }
}

@keyframes slice5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(5px, 5px);
  }
}

@keyframes slice4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-5px, 5px);
  }
}

@keyframes slice3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-5px, -5px);
  }
}

@keyframes slice2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, 5px);
  }
}

@keyframes slice1 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, -5px);
  }
}

@keyframes pepperoni {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-2px, -2px);
  }
}
@keyframes pepperoni_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(2px, -2px);
  }
}
@keyframes pepperoni_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-2px, 2px);
  }
}
@keyframes pepperoni_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(2px, 2px);
  }
}
@keyframes pepperoni_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-2px, 0);
  }
}
@keyframes pepperoni_6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(2px, 0);
  }
}

@keyframes mushroom {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1px, -1px);
  }
}
@keyframes mushroom_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1px, -1px);
  }
}
@keyframes mushroom_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1px, 1px);
  }
}
@keyframes mushroom_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1px, 1px);
  }
}
@keyframes mushroom_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, -1px);
  }
}

@keyframes onion {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-0.5px, -0.5px);
  }
}
@keyframes onion_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0.5px, -0.5px);
  }
}
@keyframes onion_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-0.5px, 0.5px);
  }
}
@keyframes onion_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0.5px, 0.5px);
  }
}
@keyframes onion_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, -0.5px);
  }
}
@keyframes onion_6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(0, 0.5px);
  }
}

@keyframes pepper {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1.5px, -1.5px);
  }
}
@keyframes pepper_2 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.5px, -1.5px);
  }
}
@keyframes pepper_3 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1.5px, 1.5px);
  }
}
@keyframes pepper_4 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.5px, 1.5px);
  }
}
@keyframes pepper_5 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1.5px, 0);
  }
}
@keyframes pepper_6 {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.5px, 0);
  }
}

/* Water Wave Effect Styles */
.e-card {
  margin: 100px auto;
  background: transparent;
  box-shadow: 0px 8px 28px -9px rgba(0,0,0,0.45);
  position: relative;
  width: 240px;
  height: 330px;
  border-radius: 16px;
  overflow: hidden;
}

.wave {
  position: absolute;
  width: 540px;
  height: 700px;
  opacity: 0.6;
  left: 0;
  top: 0;
  margin-left: -50%;
  margin-top: -70%;
  background: linear-gradient(744deg,#af40ff,#5b42f3 60%,#00ddeb);
}

.icon {
  width: 3em;
  margin-top: -1em;
  padding-bottom: 1em;
}

.infotop {
  text-align: center;
  font-size: 20px;
  position: absolute;
  top: 5.6em;
  left: 0;
  right: 0;
  color: rgb(255, 255, 255);
  font-weight: 600;
}

.name {
  font-size: 14px;
  font-weight: 100;
  position: relative;
  top: 1em;
  text-transform: lowercase;
}

.wave:nth-child(2),
.wave:nth-child(3) {
  top: 210px;
}

.playing .wave {
  border-radius: 40%;
  animation: wave 3000ms infinite linear;
}

.wave {
  border-radius: 40%;
  animation: wave 55s infinite linear;
}

.playing .wave:nth-child(2) {
  animation-duration: 4000ms;
}

.wave:nth-child(2) {
  animation-duration: 50s;
}

.playing .wave:nth-child(3) {
  animation-duration: 5000ms;
}

.wave:nth-child(3) {
  animation-duration: 45s;
}

@keyframes wave {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.el-row {
  width: 100%;
}

.empty-data,
.empty-analysis {
  min-height: 0;
}

.quick-import h4 {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--dash-muted);
  font-weight: 500;
}

.reminder-item,
.knowledge-item {
  gap: 10px;
}

.knowledge-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f3f7;
}

.knowledge-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.knowledge-title {
  font-weight: 600;
  color: var(--dash-text);
  margin-bottom: 4px;
}

.knowledge-desc {
  color: var(--dash-muted);
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 1280px) {
  .dashboard-body {
    grid-template-columns: minmax(0, 1fr) minmax(240px, 280px);
  }

  .metric-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  }

  .metric-strip-more {
    grid-column: 1 / -1;
    justify-self: start;
  }
}

@media (max-width: 1100px) {
  .dashboard-body {
    grid-template-columns: 1fr;
  }

  .dashboard-aside {
    position: static;
  }

  .entry-rail {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .metric-strip {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 992px) {
  .welcome-panel {
    flex-direction: column;
    align-items: flex-start;
  }

  .welcome-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .chart-container,
  .chart {
    min-height: 180px;
    height: 200px;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 0 0 12px;
  }

  .welcome-panel {
    padding: 12px 14px;
  }

  .welcome-panel h2 {
    font-size: 18px;
  }

  .welcome-actions :deep(.el-button) {
    flex: 1 1 auto;
  }
}

</style>
