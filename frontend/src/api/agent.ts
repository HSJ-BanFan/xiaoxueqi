import type { AxiosResponse } from 'axios'

import { apiClient } from './index'

export interface AgentHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AgentChatRequest {
  message: string
  conversation_id?: string | null
  history?: AgentHistoryMessage[]
  confirm_write?: boolean
}

export interface AgentToolCall {
  id?: string | null
  name: string
  arguments: Record<string, unknown>
}

export interface ToolResult {
  name: string
  ok: boolean
  data?: unknown
  error?: string | null
  requires_confirm?: boolean
}

export interface AgentChatResponse {
  reply: string
  conversation_id: string
  mode: 'agent' | 'fallback' | 'disabled'
  model?: string | null
  rounds: number
  tool_calls: AgentToolCall[]
  tool_results: ToolResult[]
  disclaimer: string
}

const AGENT_TIMEOUT_MS = 90_000

export const agentApi = {
  chat(payload: AgentChatRequest): Promise<AxiosResponse<AgentChatResponse>> {
    return apiClient.post<AgentChatResponse>('/api/v1/agent/chat', payload, {
      timeout: AGENT_TIMEOUT_MS
    })
  }
}

export default agentApi
