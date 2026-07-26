<template>
  <div class="settings-container">
    <div class="page-heading">
      <div>
        <h1>账户设置</h1>
        <p>维护基础资料和健康档案，让助理与血糖图表使用更准确的信息。</p>
      </div>
    </div>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>个人资料</span>
            <small>姓名、联系方式与基础信息</small>
          </div>
        </div>
      </template>

      <el-form
        ref="personalFormRef"
        v-loading="profileFetching"
        :model="personalForm"
        :rules="personalRules"
        label-width="100px"
        status-icon
      >
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="personalForm.name" maxlength="100" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="personalForm.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="手机号码" prop="phone">
              <el-input v-model="personalForm.phone" maxlength="20" placeholder="选填" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="出生日期" prop="birth_date">
              <el-date-picker
                v-model="personalForm.birth_date"
                type="date"
                placeholder="选择出生日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disableFutureDate"
                class="full-width"
              />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="personalForm.gender" clearable placeholder="选填" class="full-width">
                <el-option label="男" value="male" />
                <el-option label="女" value="female" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item class="form-actions">
          <el-button type="primary" :loading="personalSaving" @click="savePersonalProfile">
            保存个人资料
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card id="health-profile" class="settings-card health-profile-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>健康档案</span>
            <small>用于健康管理展示，不作为医疗诊断依据</small>
          </div>
          <el-tag :type="healthProfileIncomplete ? 'warning' : 'success'" effect="light">
            {{ healthProfileIncomplete ? '待完善' : '已完善' }}
          </el-tag>
        </div>
      </template>

      <el-alert
        v-if="healthProfileIncomplete"
        class="profile-tip"
        title="完善档案后助理与图表更准"
        description="建议至少设置糖尿病类型和目标血糖上下限。"
        type="warning"
        :closable="false"
        show-icon
      />

      <el-form
        ref="healthFormRef"
        v-loading="profileFetching"
        :model="healthForm"
        :rules="healthRules"
        label-width="120px"
        status-icon
      >
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="糖尿病类型" prop="diabetes_type">
              <el-select
                v-model="healthForm.diabetes_type"
                clearable
                placeholder="请选择类型"
                class="full-width"
              >
                <el-option
                  v-for="option in diabetesTypeOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="确诊日期" prop="diagnosis_date">
              <el-date-picker
                v-model="healthForm.diagnosis_date"
                type="date"
                placeholder="选填"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disableFutureDate"
                class="full-width"
              />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="身高" prop="height">
              <el-input-number
                v-model="healthForm.height"
                :min="50"
                :max="250"
                :precision="1"
                :step="0.5"
                controls-position="right"
                class="full-width"
              />
              <span class="unit-hint">cm（50–250）</span>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="体重" prop="weight">
              <el-input-number
                v-model="healthForm.weight"
                :min="20"
                :max="300"
                :precision="1"
                :step="0.5"
                controls-position="right"
                class="full-width"
              />
              <span class="unit-hint">kg（20–300）</span>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="目标血糖下限" prop="target_glucose_min">
              <el-input-number
                v-model="healthForm.target_glucose_min"
                :min="1"
                :max="30"
                :precision="1"
                :step="0.1"
                controls-position="right"
                class="full-width"
              />
              <span class="unit-hint">mmol/L（1–30）</span>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="目标血糖上限" prop="target_glucose_max">
              <el-input-number
                v-model="healthForm.target_glucose_max"
                :min="1"
                :max="30"
                :precision="1"
                :step="0.1"
                controls-position="right"
                class="full-width"
              />
              <span class="unit-hint">需高于下限</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item class="form-actions">
          <el-button type="primary" :loading="healthSaving" @click="saveHealthProfile">
            保存健康档案
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>修改密码</span>
            <small>密码更新与个人资料、健康档案分别提交</small>
          </div>
        </div>
      </template>

      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            autocomplete="new-password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item class="form-actions">
          <el-button type="primary" :loading="passwordLoading" @click="updatePassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>通知设置</span>
            <small>本地界面偏好</small>
          </div>
        </div>
      </template>

      <el-form :model="notificationForm" label-width="100px">
        <el-form-item label="邮件通知">
          <el-switch v-model="notificationForm.emailEnabled" />
        </el-form-item>
        <el-form-item label="血糖提醒">
          <el-switch v-model="notificationForm.glucoseReminder" />
        </el-form-item>
        <el-form-item label="药物提醒">
          <el-switch v-model="notificationForm.medicationReminder" />
        </el-form-item>
        <el-form-item label="健康报告">
          <el-switch v-model="notificationForm.healthReport" />
        </el-form-item>
        <el-form-item class="form-actions">
          <el-button type="primary" :loading="notificationLoading" @click="updateNotificationSettings">
            保存通知设置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card danger-zone">
      <template #header>
        <div class="card-header">
          <span>账户操作</span>
        </div>
      </template>

      <div class="danger-actions">
        <div class="danger-action">
          <div class="danger-info">
            <h4>退出登录</h4>
            <p>退出当前账号的登录状态。</p>
          </div>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>

        <div class="danger-action">
          <div class="danger-info">
            <h4>删除账户</h4>
            <p>当前版本尚未开放账户删除接口。</p>
          </div>
          <el-button type="danger" plain @click="showDeleteAccountNotice">删除账户</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { isAxiosError } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import type { DiabetesType, Gender, User, UserUpdate, ValidationError } from '../types/models'

interface PersonalForm {
  name: string
  email: string
  phone: string
  birth_date: string
  gender: Gender | ''
}

interface HealthForm {
  diabetes_type: DiabetesType | ''
  diagnosis_date: string
  height?: number
  weight?: number
  target_glucose_min?: number
  target_glucose_max?: number
}

interface PasswordForm {
  newPassword: string
  confirmPassword: string
}

interface ApiErrorBody {
  detail?: string | ValidationError[] | Record<string, unknown>
}

const route = useRoute()
const userStore = useUserStore()

const personalFormRef = ref<FormInstance>()
const healthFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

const profileFetching = ref(false)
const personalSaving = ref(false)
const healthSaving = ref(false)
const passwordLoading = ref(false)
const notificationLoading = ref(false)
const mountedOnce = ref(false)

const personalForm = reactive<PersonalForm>({
  name: '',
  email: '',
  phone: '',
  birth_date: '',
  gender: ''
})

const healthForm = reactive<HealthForm>({
  diabetes_type: '',
  diagnosis_date: '',
  height: undefined,
  weight: undefined,
  target_glucose_min: undefined,
  target_glucose_max: undefined
})

const passwordForm = reactive<PasswordForm>({
  newPassword: '',
  confirmPassword: ''
})

const notificationForm = reactive({
  emailEnabled: true,
  glucoseReminder: true,
  medicationReminder: false,
  healthReport: true
})

const diabetesTypeOptions: Array<{ value: DiabetesType; label: string }> = [
  { value: 'type1', label: '1 型糖尿病' },
  { value: 'type2', label: '2 型糖尿病' },
  { value: 'gestational', label: '妊娠期糖尿病' },
  { value: 'prediabetes', label: '糖尿病前期' },
  { value: 'other', label: '其他' }
]

const healthProfileIncomplete = computed(
  () =>
    !healthForm.diabetes_type ||
    healthForm.target_glucose_min === undefined ||
    healthForm.target_glucose_max === undefined
)

const validatePhone = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!value || /^1[3-9]\d{9}$/.test(value) || /^[+\d][\d\s-]{5,19}$/.test(value)) {
    callback()
    return
  }
  callback(new Error('请输入正确的手机号码'))
}

const validateNumberRange = (label: string, min: number, max: number) => {
  return (_rule: unknown, value: unknown, callback: (error?: Error) => void) => {
    if (value === undefined || value === null || value === '') {
      callback()
      return
    }

    const numericValue = Number(value)
    if (!Number.isFinite(numericValue) || numericValue < min || numericValue > max) {
      callback(new Error(`${label}需在 ${min}–${max} 之间`))
      return
    }
    callback()
  }
}

const validateTargetRange = (_rule: unknown, _value: unknown, callback: (error?: Error) => void) => {
  const min = healthForm.target_glucose_min
  const max = healthForm.target_glucose_max

  if (min === undefined && max === undefined) {
    callback()
    return
  }
  if (min === undefined || max === undefined) {
    callback(new Error('请同时填写目标血糖上下限'))
    return
  }
  if (!Number.isFinite(min) || !Number.isFinite(max) || min < 1 || min > 30 || max < 1 || max > 30) {
    callback(new Error('目标血糖需在 1–30 mmol/L 之间'))
    return
  }
  if (min >= max) {
    callback(new Error('目标血糖下限必须低于上限'))
    return
  }
  callback()
}

const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const personalRules: FormRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 1, max: 100, message: '姓名长度需在 1–100 个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
  ],
  phone: [{ validator: validatePhone, trigger: ['blur', 'change'] }]
}

const healthRules: FormRules = {
  height: [{ validator: validateNumberRange('身高', 50, 250), trigger: 'change' }],
  weight: [{ validator: validateNumberRange('体重', 20, 300), trigger: 'change' }],
  target_glucose_min: [{ validator: validateTargetRange, trigger: 'change' }],
  target_glucose_max: [{ validator: validateTargetRange, trigger: 'change' }]
}

const passwordRules: FormRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: ['blur', 'change'] }
  ]
}

const disableFutureDate = (date: Date) => date.getTime() > Date.now()

const toDateInput = (value?: string | null) => (value ? value.slice(0, 10) : '')
const toApiDateTime = (value: string) => (value ? `${value}T00:00:00` : undefined)

const fillForms = (profile: User) => {
  personalForm.name = profile.name || ''
  personalForm.email = profile.email || ''
  personalForm.phone = profile.phone || ''
  personalForm.birth_date = toDateInput(profile.birth_date)
  personalForm.gender = profile.gender || ''

  healthForm.diabetes_type = profile.diabetes_type || ''
  healthForm.diagnosis_date = toDateInput(profile.diagnosis_date)
  healthForm.height = profile.height ?? undefined
  healthForm.weight = profile.weight ?? undefined
  healthForm.target_glucose_min = profile.target_glucose_min ?? undefined
  healthForm.target_glucose_max = profile.target_glucose_max ?? undefined
}

const validateForm = async (form?: FormInstance) => {
  if (!form) return false
  try {
    await form.validate()
    return true
  } catch {
    return false
  }
}

const formatApiError = (error: unknown, fallback: string) => {
  if (!isAxiosError<ApiErrorBody>(error)) {
    return error instanceof Error ? error.message : fallback
  }

  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        const field = item.loc?.filter(part => part !== 'body').join('.')
        return field ? `${field}：${item.msg}` : item.msg
      })
      .filter(Boolean)
      .join('；') || fallback
  }

  if (detail && typeof detail === 'object') {
    return Object.entries(detail)
      .map(([key, value]) => `${key}：${String(value)}`)
      .join('；')
  }

  return fallback
}

const loadProfile = async () => {
  profileFetching.value = true
  try {
    const profile = await userStore.fetchProfile()
    if (!profile) throw new Error('未获取到用户资料')
    fillForms(profile)
  } catch (error) {
    ElMessage.error(formatApiError(error, '获取用户资料失败，请稍后重试'))
  } finally {
    profileFetching.value = false
  }
}

const savePersonalProfile = async () => {
  if (!(await validateForm(personalFormRef.value))) return

  const payload: UserUpdate = {
    name: personalForm.name.trim(),
    email: personalForm.email.trim(),
    phone: personalForm.phone.trim()
  }
  if (personalForm.birth_date) payload.birth_date = toApiDateTime(personalForm.birth_date)
  if (personalForm.gender) payload.gender = personalForm.gender

  personalSaving.value = true
  try {
    const profile = await userStore.updateProfile(payload)
    fillForms(profile)
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    ElMessage.error(formatApiError(error, '个人资料更新失败'))
  } finally {
    personalSaving.value = false
  }
}

const saveHealthProfile = async () => {
  if (!(await validateForm(healthFormRef.value))) return

  const payload: UserUpdate = {}
  if (healthForm.diabetes_type) payload.diabetes_type = healthForm.diabetes_type
  if (healthForm.diagnosis_date) payload.diagnosis_date = toApiDateTime(healthForm.diagnosis_date)
  if (healthForm.height !== undefined) payload.height = healthForm.height
  if (healthForm.weight !== undefined) payload.weight = healthForm.weight
  if (healthForm.target_glucose_min !== undefined) {
    payload.target_glucose_min = healthForm.target_glucose_min
  }
  if (healthForm.target_glucose_max !== undefined) {
    payload.target_glucose_max = healthForm.target_glucose_max
  }

  healthSaving.value = true
  try {
    const profile = await userStore.updateProfile(payload)
    fillForms(profile)
    ElMessage.success('健康档案更新成功')
  } catch (error) {
    ElMessage.error(formatApiError(error, '健康档案更新失败'))
  } finally {
    healthSaving.value = false
  }
}

const updatePassword = async () => {
  if (!(await validateForm(passwordFormRef.value))) return

  passwordLoading.value = true
  try {
    await userStore.updateProfile({ password: passwordForm.newPassword })
    passwordFormRef.value?.resetFields()
    ElMessage.success('密码修改成功')
  } catch (error) {
    ElMessage.error(formatApiError(error, '密码修改失败'))
  } finally {
    passwordLoading.value = false
  }
}

const updateNotificationSettings = async () => {
  notificationLoading.value = true
  await Promise.resolve()
  notificationLoading.value = false
  ElMessage.success('通知设置已保存在当前页面')
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => userStore.logout())
    .catch(() => undefined)
}

const showDeleteAccountNotice = () => {
  ElMessage.info('当前版本尚未开放账户删除功能')
}

const scrollToHealthProfile = () => {
  if (route.hash !== '#health-profile') return
  void nextTick(() => {
    document.getElementById('health-profile')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

watch(
  () => route.fullPath,
  (_fullPath, previousFullPath) => {
    if (mountedOnce.value && route.path === '/settings' && !previousFullPath.startsWith('/settings')) {
      void loadProfile()
    }
    scrollToHealthProfile()
  }
)

onMounted(async () => {
  await loadProfile()
  mountedOnce.value = true
  scrollToHealthProfile()
})
</script>

<style scoped>
.settings-container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 20px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-heading h1 {
  margin: 0 0 8px;
  color: #303133;
  font-size: 28px;
}

.page-heading p {
  margin: 0;
  color: #909399;
  line-height: 1.6;
}

.settings-card {
  margin-bottom: 20px;
  scroll-margin-top: 20px;
}

.health-profile-card {
  border-top: 3px solid #409eff;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-weight: 600;
}

.card-header > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-header small {
  color: #909399;
  font-size: 12px;
  font-weight: 400;
}

.profile-tip {
  margin-bottom: 22px;
}

.full-width {
  width: 100%;
}

.unit-hint {
  display: block;
  width: 100%;
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}

.form-actions {
  margin-top: 4px;
  margin-bottom: 0;
}

.danger-zone {
  border: 1px solid #fbc4c4;
}

.danger-actions {
  display: flex;
  flex-direction: column;
}

.danger-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.danger-action:last-child {
  border-bottom: none;
}

.danger-info h4 {
  margin: 0 0 5px;
  color: #f56c6c;
}

.danger-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

@media (max-width: 768px) {
  .settings-container {
    padding: 12px;
  }

  .page-heading h1 {
    font-size: 24px;
  }

  :deep(.el-form-item) {
    display: block;
  }

  :deep(.el-form-item__label) {
    width: auto !important;
    margin-bottom: 6px;
    line-height: 1.4;
  }

  :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }

  .danger-action {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
