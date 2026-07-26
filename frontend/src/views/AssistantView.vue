<template>
  <div class="assistant-page">
    <header class="assistant-header">
      <div>
        <div class="eyebrow">Health Agent</div>
        <h2>智能健康助理</h2>
        <p>查询真实健康数据，写入操作由您确认后执行。</p>
      </div>
      <el-button plain :disabled="loading" @click="startNewConversation">
        新对话
      </el-button>
    </header>

    <main ref="chatBodyRef" class="chat-body">
      <section v-if="messages.length === 0" class="welcome-panel">
        <div class="welcome-icon">
          <el-icon :size="42"><ChatLineRound /></el-icon>
        </div>
        <h3>您好，我是小雪琪</h3>
        <p>
          我可以读取您的血糖记录、生成统计摘要，并在您确认后记录新的血糖数据。
        </p>
        <el-tag type="success" effect="plain">默认使用 Agent 主路径</el-tag>
      </section>

      <section
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role === 'user' ? 'message-row--user' : 'message-row--assistant'"
      >
        <el-avatar v-if="message.role === 'user'" :size="36" :src="userAvatar">
          {{ userInitial }}
        </el-avatar>
        <el-avatar v-else :size="36" src="/assistant-avatar.png">小雪琪</el-avatar>

        <article class="message-card" :class="{ 'message-card--error': message.isError }">
          <div v-if="message.role === 'assistant' && message.mode" class="message-meta">
            <el-tag :type="modeMeta[message.mode].type" size="small" effect="light">
              {{ modeMeta[message.mode].label }}
            </el-tag>
            <span v-if="message.model">{{ message.model }}</span>
            <span v-if="message.rounds !== undefined">{{ message.rounds }} 轮</span>
          </div>

          <div
            v-if="message.role === 'assistant'"
            class="message-text markdown-body"
            v-html="formatMessage(message.content)"
          ></div>
          <div v-else class="message-text">{{ message.content }}</div>

          <el-collapse
            v-if="hasToolTrace(message)"
            class="tool-trace"
          >
            <el-collapse-item :name="message.id">
              <template #title>
                <span class="tool-trace-title">
                  <el-icon><Operation /></el-icon>
                  工具轨迹 · {{ getToolTraces(message).length }}
                </span>
              </template>

              <div
                v-for="(trace, traceIndex) in getToolTraces(message)"
                :key="`${message.id}-tool-${traceIndex}`"
                class="tool-trace-item"
              >
                <div class="tool-trace-heading">
                  <code>{{ trace.name }}</code>
                  <el-tag
                    v-if="trace.result"
                    :type="trace.result.ok ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ trace.result.ok ? '成功' : '失败' }}
                  </el-tag>
                  <el-tag v-if="trace.result?.requires_confirm" type="warning" size="small">
                    待确认
                  </el-tag>
                </div>
                <div class="tool-trace-block">
                  <span>参数</span>
                  <pre>{{ formatJsonSummary(trace.arguments) }}</pre>
                </div>
                <div v-if="trace.result" class="tool-trace-block">
                  <span>{{ trace.result.ok ? '结果' : '错误' }}</span>
                  <pre :class="{ 'tool-error': !trace.result.ok }">{{ formatToolResult(trace.result) }}</pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <div
            v-if="message.confirmation"
            class="confirmation-card"
            :class="`confirmation-card--${message.confirmation.status}`"
          >
            <div class="confirmation-heading">
              <el-icon><Warning /></el-icon>
              <strong>写入前确认</strong>
            </div>
            <p class="confirmation-note">当前尚未写入数据库，请核对以下内容：</p>
            <pre>{{ message.confirmation.preview }}</pre>
            <div class="confirmation-actions">
              <el-button
                type="primary"
                :loading="confirmingMessageId === message.id"
                :disabled="loading || message.confirmation.status === 'confirmed'"
                @click="confirmWrite(message)"
              >
                {{ message.confirmation.status === 'confirmed' ? '已确认写入' : '确认写入' }}
              </el-button>
              <span v-if="message.confirmation.status === 'confirmed'" class="confirmation-success">
                写入请求已成功执行
              </span>
              <span v-else-if="message.confirmation.status === 'failed'" class="confirmation-failed">
                写入未完成，请重试
              </span>
            </div>
          </div>

          <time class="message-time">{{ formatTime(message.timestamp) }}</time>
        </article>
      </section>

      <div v-if="loading" class="typing-row" aria-label="助理正在回复">
        <el-avatar :size="36" src="/assistant-avatar.png">小雪琪</el-avatar>
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </main>

    <section class="quick-actions" aria-label="快捷提问">
      <span class="quick-actions-label">快捷提问</span>
      <el-button
        v-for="shortcut in shortcuts"
        :key="shortcut.label"
        round
        size="small"
        :disabled="loading"
        @click="useShortcut(shortcut)"
      >
        {{ shortcut.label }}
      </el-button>
    </section>

    <section class="composer">
      <el-input
        ref="inputRef"
        v-model="userInput"
        type="textarea"
        :rows="2"
        maxlength="4000"
        show-word-limit
        placeholder="例如：本周血糖统计"
        resize="none"
        @keydown.enter.prevent="handleEnterKey"
      />
      <div class="composer-actions">
        <span>Enter 发送，Shift + Enter 换行</span>
        <el-button
          type="primary"
          :loading="loading && !confirmingMessageId"
          :disabled="!userInput.trim() || loading"
          @click="sendMessage()"
        >
          发送
        </el-button>
      </div>
    </section>

    <footer class="disclaimer-bar">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ disclaimer }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatLineRound,
  InfoFilled,
  Operation,
  Warning
} from '@element-plus/icons-vue'
import { marked } from 'marked'

import { agentApi } from '../api/agent'
import type {
  AgentChatResponse,
  AgentHistoryMessage,
  AgentToolCall,
  ToolResult
} from '../api/agent'
import { useUserStore } from '../stores/user'

type AgentMode = AgentChatResponse['mode']
type ConfirmationStatus = 'pending' | 'submitting' | 'confirmed' | 'failed'
type TagType = 'success' | 'warning' | 'info' | 'danger'

interface ConfirmationState {
  originalMessage: string
  preview: string
  status: ConfirmationStatus
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  mode?: AgentMode
  model?: string | null
  rounds?: number
  toolCalls?: AgentToolCall[]
  toolResults?: ToolResult[]
  confirmation?: ConfirmationState
  includeInHistory?: boolean
  isError?: boolean
}

interface Shortcut {
  label: string
  prompt: string
  action: 'send' | 'prefill'
}

interface ToolTrace {
  name: string
  arguments: Record<string, unknown>
  result?: ToolResult
}

const FALLBACK_DISCLAIMER =
  '说明：我是健康管理助手，不是执业医师。内容仅用于健康管理参考，不能替代诊断或治疗；如有急症请及时就医。'

const modeMeta: Record<AgentMode, { label: string; type: TagType }> = {
  agent: { label: 'Agent', type: 'success' },
  fallback: { label: '规则模式', type: 'warning' },
  disabled: { label: '已关闭', type: 'info' }
}

const measurementTimeLabels: Record<string, string> = {
  BEFORE_BREAKFAST: '早餐前 / 空腹',
  AFTER_BREAKFAST: '早餐后',
  BEFORE_LUNCH: '午餐前',
  AFTER_LUNCH: '午餐后',
  BEFORE_DINNER: '晚餐前',
  AFTER_DINNER: '晚餐后',
  BEFORE_SLEEP: '睡前',
  MIDNIGHT: '凌晨',
  OTHER: '其他'
}

const shortcuts: Shortcut[] = [
  { label: '最近血糖', prompt: '最近血糖', action: 'send' },
  { label: '本周血糖统计', prompt: '本周血糖统计', action: 'send' },
  { label: '记录血糖引导', prompt: '记录血糖 6.5 空腹', action: 'prefill' }
]

const route = useRoute()
const userStore = useUserStore()
const chatBodyRef = ref<HTMLElement | null>(null)
const inputRef = ref<{ focus: () => void } | null>(null)
const messages = ref<ChatMessage[]>([])
const userInput = ref('')
const loading = ref(false)
const confirmingMessageId = ref<string | null>(null)
const currentConversationId = ref<string | null>(null)
const disclaimer = ref(FALLBACK_DISCLAIMER)
let messageSequence = 0

const userAvatar = computed(() => userStore.user?.avatar || '')
const userInitial = computed(() => {
  const name = userStore.user?.name || userStore.user?.email || '用户'
  return name.charAt(0).toUpperCase()
})

onMounted(() => {
  const prefill = route.query.prefill
  if (typeof prefill === 'string') {
    userInput.value = prefill.slice(0, 4000)
    nextTick(() => inputRef.value?.focus())
  }
})

const makeMessageId = (prefix: string) => {
  messageSequence += 1
  return `${prefix}-${Date.now()}-${messageSequence}`
}

const buildHistory = (): AgentHistoryMessage[] => {
  return messages.value
    .filter(message => message.includeInHistory !== false)
    .map(message => ({ role: message.role, content: message.content.slice(0, 12000) }))
    .slice(-50)
}

const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) return
  sendMessage()
}

const useShortcut = (shortcut: Shortcut) => {
  if (shortcut.action === 'prefill') {
    userInput.value = shortcut.prompt
    nextTick(() => inputRef.value?.focus())
    return
  }

  sendMessage(shortcut.prompt)
}

const sendMessage = async (text?: string) => {
  const messageText = (text ?? userInput.value).trim()
  if (!messageText || loading.value) return

  const history = buildHistory()
  messages.value.push({
    id: makeMessageId('user'),
    role: 'user',
    content: messageText,
    timestamp: new Date().toISOString()
  })

  userInput.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const response = await agentApi.chat({
      message: messageText,
      conversation_id: currentConversationId.value,
      history,
      confirm_write: false
    })
    appendAgentResponse(response.data, messageText)
  } catch (error: unknown) {
    appendRequestError(error)
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const appendAgentResponse = (response: AgentChatResponse, originalMessage: string) => {
  currentConversationId.value = response.conversation_id
  disclaimer.value = response.disclaimer || FALLBACK_DISCLAIMER

  const pendingResult = response.tool_results.find(result => result.requires_confirm === true)
  messages.value.push({
    id: makeMessageId('assistant'),
    role: 'assistant',
    content: response.reply,
    timestamp: new Date().toISOString(),
    mode: response.mode,
    model: response.model,
    rounds: response.rounds,
    toolCalls: response.tool_calls,
    toolResults: response.tool_results,
    confirmation: pendingResult
      ? {
          originalMessage,
          preview: buildConfirmationPreview(pendingResult, response.reply),
          status: 'pending'
        }
      : undefined
  })
}

const confirmWrite = async (message: ChatMessage) => {
  const confirmation = message.confirmation
  if (!confirmation || loading.value || confirmation.status === 'confirmed') return

  confirmation.status = 'submitting'
  confirmingMessageId.value = message.id
  loading.value = true

  try {
    const response = await agentApi.chat({
      message: confirmation.originalMessage,
      conversation_id: currentConversationId.value,
      confirm_write: true
    })

    currentConversationId.value = response.data.conversation_id
    disclaimer.value = response.data.disclaimer || FALLBACK_DISCLAIMER

    const writeResult = response.data.tool_results.find(
      result => result.name === 'add_glucose_record'
    )
    const writeSucceeded = Boolean(
      writeResult?.ok && writeResult.requires_confirm !== true
    )

    appendAgentResponse(response.data, confirmation.originalMessage)

    if (writeSucceeded) {
      confirmation.status = 'confirmed'
      ElMessage.success('血糖记录已确认写入')
    } else {
      confirmation.status = 'failed'
      ElMessage.error(writeResult?.error || '写入未完成，请核对助理回复后重试')
    }
  } catch (error: unknown) {
    confirmation.status = 'failed'
    appendRequestError(error)
  } finally {
    confirmingMessageId.value = null
    loading.value = false
    scrollToBottom()
  }
}

const appendRequestError = (error: unknown) => {
  const errorMessage = getErrorMessage(error)
  const status = axios.isAxiosError(error) ? error.response?.status : undefined

  if (status === 401) {
    ElMessage.warning(errorMessage)
  } else {
    ElMessage.error(errorMessage)
  }

  messages.value.push({
    id: makeMessageId('error'),
    role: 'assistant',
    content: errorMessage,
    timestamp: new Date().toISOString(),
    includeInHistory: false,
    isError: true
  })
}

const getErrorMessage = (error: unknown): string => {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : '发送失败，请稍后重试。'
  }

  const status = error.response?.status
  if (status === 401) {
    return '登录状态已过期，正在跳转登录页，请重新登录。'
  }
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT' || /timeout/i.test(error.message)) {
    return '助理响应超时（90 秒），请稍后重试或缩短问题。'
  }
  if (!error.response) {
    return '无法连接后端服务，请检查网络、API 地址与后端是否已启动。'
  }

  const detail = (error.response.data as { detail?: unknown; message?: unknown } | undefined)
  const serverMessage = detail?.detail ?? detail?.message
  if (typeof serverMessage === 'string' && serverMessage.trim()) {
    return `请求失败：${serverMessage}`
  }

  return `请求失败（HTTP ${status ?? '未知'}），请稍后重试。`
}

const startNewConversation = async () => {
  if (messages.value.length > 0) {
    try {
      await ElMessageBox.confirm(
        '这会清空当前页面中的对话，并开始一个新的 Agent 会话。',
        '开始新对话',
        {
          confirmButtonText: '开始新对话',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }

  messages.value = []
  currentConversationId.value = null
  disclaimer.value = FALLBACK_DISCLAIMER
  userInput.value = ''
  ElMessage.success('已开始新对话')
}

const hasToolTrace = (message: ChatMessage) => {
  return Boolean(message.toolCalls?.length || message.toolResults?.length)
}

const getToolTraces = (message: ChatMessage): ToolTrace[] => {
  const toolCalls = message.toolCalls || []
  const toolResults = message.toolResults || []
  const count = Math.max(toolCalls.length, toolResults.length)

  return Array.from({ length: count }, (_, index) => ({
    name: toolCalls[index]?.name || toolResults[index]?.name || `tool_${index + 1}`,
    arguments: toolCalls[index]?.arguments || {},
    result: toolResults[index]
  }))
}

const formatToolResult = (result: ToolResult) => {
  if (!result.ok) return result.error || '工具执行失败'
  if (result.data === undefined || result.data === null) return '执行成功'
  return formatJsonSummary(result.data)
}

const formatJsonSummary = (value: unknown) => {
  try {
    const formatted = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
    if (!formatted) return '—'
    return formatted.length > 800 ? `${formatted.slice(0, 800)}…` : formatted
  } catch {
    return String(value)
  }
}

const buildConfirmationPreview = (result: ToolResult, reply: string) => {
  if (isRecord(result.data)) {
    const rawPreview = isRecord(result.data.preview) ? result.data.preview : result.data
    const lines: string[] = []

    if (rawPreview.value !== undefined) {
      lines.push(`血糖值：${rawPreview.value} mmol/L`)
    }
    if (typeof rawPreview.measurement_time === 'string') {
      const label = measurementTimeLabels[rawPreview.measurement_time] || rawPreview.measurement_time
      lines.push(`测量时段：${label}`)
    }
    if (typeof rawPreview.measurement_method === 'string') {
      lines.push(`测量方式：${rawPreview.measurement_method}`)
    }
    if (typeof rawPreview.notes === 'string' && rawPreview.notes.trim()) {
      lines.push(`备注：${rawPreview.notes}`)
    }

    if (lines.length > 0) return lines.join('\n')
    return formatJsonSummary(rawPreview)
  }

  return reply.replace(FALLBACK_DISCLAIMER, '').trim() || '请确认是否执行本次写入。'
}

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

const escapeHtml = (text: string) => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

const formatMessage = (text: string) => {
  try {
    return marked.parse(escapeHtml(text), { breaks: true, gfm: true }) as string
  } catch {
    return escapeHtml(text).replace(/\n/g, '<br>')
  }
}

const formatTime = (timestamp: string) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(new Date(timestamp))
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.assistant-page {
  --assistant-primary: #2563eb;
  --assistant-primary-soft: #eff6ff;
  --assistant-border: #e5e7eb;
  --assistant-text: #1f2937;
  --assistant-muted: #64748b;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 96px);
  padding: 24px;
  color: var(--assistant-text);
  background: #f4f7fb;
}

.assistant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 24px;
  border: 1px solid var(--assistant-border);
  border-radius: 18px 18px 0 0;
  background: #ffffff;
}

.assistant-header h2 {
  margin: 2px 0 6px;
  font-size: 24px;
}

.assistant-header p {
  margin: 0;
  color: var(--assistant-muted);
}

.eyebrow {
  color: var(--assistant-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.chat-body {
  flex: 1;
  min-height: 360px;
  max-height: calc(100vh - 390px);
  overflow-y: auto;
  padding: 24px;
  border-right: 1px solid var(--assistant-border);
  border-left: 1px solid var(--assistant-border);
  background: #ffffff;
  scroll-behavior: smooth;
}

.welcome-panel {
  display: flex;
  min-height: 300px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.welcome-panel h3 {
  margin: 14px 0 8px;
  font-size: 24px;
}

.welcome-panel p {
  max-width: 620px;
  margin: 0 0 18px;
  color: var(--assistant-muted);
  line-height: 1.7;
}

.welcome-icon {
  display: grid;
  width: 72px;
  height: 72px;
  place-items: center;
  border-radius: 24px;
  color: var(--assistant-primary);
  background: var(--assistant-primary-soft);
}

.message-row,
.typing-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 22px;
}

.message-row--user {
  flex-direction: row-reverse;
}

.message-card {
  width: fit-content;
  max-width: min(760px, 78%);
  padding: 14px 16px 10px;
  border: 1px solid var(--assistant-border);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.message-row--user .message-card {
  border-color: #bfdbfe;
  background: var(--assistant-primary-soft);
}

.message-card--error {
  border-color: #fecaca;
  color: #991b1b;
  background: #fef2f2;
}

.message-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 9px;
  color: var(--assistant-muted);
  font-size: 12px;
}

.message-text {
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.7;
}

.markdown-body {
  white-space: normal;
}

.markdown-body :deep(p) {
  margin: 0 0 10px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 22px;
}

.markdown-body :deep(code) {
  padding: 2px 5px;
  border-radius: 5px;
  background: #f1f5f9;
}

.message-time {
  display: block;
  margin-top: 8px;
  color: #94a3b8;
  font-size: 11px;
  text-align: right;
}

.tool-trace {
  margin-top: 12px;
  border-top: 1px solid var(--assistant-border);
}

.tool-trace-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #475569;
  font-size: 13px;
}

.tool-trace-item {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.tool-trace-item + .tool-trace-item {
  margin-top: 10px;
}

.tool-trace-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.tool-trace-heading code {
  color: #1e40af;
  font-weight: 700;
}

.tool-trace-block > span {
  display: block;
  margin-bottom: 4px;
  color: var(--assistant-muted);
  font-size: 12px;
}

.tool-trace-block pre,
.confirmation-card pre {
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
}

.tool-trace-block + .tool-trace-block {
  margin-top: 10px;
}

.tool-error {
  color: #b91c1c;
}

.confirmation-card {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid #fbbf24;
  border-radius: 12px;
  background: #fffbeb;
}

.confirmation-card--confirmed {
  border-color: #86efac;
  background: #f0fdf4;
}

.confirmation-card--failed {
  border-color: #fca5a5;
  background: #fef2f2;
}

.confirmation-heading {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #92400e;
}

.confirmation-note {
  margin: 8px 0;
  color: #78350f;
  font-size: 13px;
}

.confirmation-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.confirmation-success {
  color: #15803d;
  font-size: 13px;
}

.confirmation-failed {
  color: #b91c1c;
  font-size: 13px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 15px 18px;
  border: 1px solid var(--assistant-border);
  border-radius: 16px;
  background: #ffffff;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing 1.2s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.3s;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border: 1px solid var(--assistant-border);
  background: #f8fafc;
}

.quick-actions-label {
  margin-right: 2px;
  color: var(--assistant-muted);
  font-size: 13px;
}

.composer {
  padding: 16px 18px 12px;
  border-right: 1px solid var(--assistant-border);
  border-left: 1px solid var(--assistant-border);
  background: #ffffff;
}

.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 10px;
  color: var(--assistant-muted);
  font-size: 12px;
}

.disclaimer-bar {
  display: flex;
  flex-shrink: 0;
  align-items: flex-start;
  gap: 8px;
  padding: 11px 18px;
  border: 1px solid #dbeafe;
  border-radius: 0 0 18px 18px;
  color: #475569;
  background: #eff6ff;
  font-size: 12px;
  line-height: 1.6;
}

.disclaimer-bar .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--assistant-primary);
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .assistant-page {
    min-height: calc(100vh - 64px);
    padding: 12px;
  }

  .assistant-header {
    align-items: flex-start;
    padding: 16px;
  }

  .assistant-header p {
    display: none;
  }

  .chat-body {
    max-height: none;
    padding: 16px 12px;
  }

  .message-card {
    max-width: calc(100% - 48px);
  }

  .composer-actions > span {
    display: none;
  }

  .composer-actions {
    justify-content: flex-end;
  }
}
</style>
