import axios from 'axios'
import type { GlucoseStatistics, User, UserCreate, UserUpdate } from '../types/models'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json'
  },
  // 添加超时设置 - 从10秒增加到20秒，大模型API调用需要更长响应时间
  timeout: 20000,
  // 添加跨域请求凭证支持
  withCredentials: true
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 401错误将由user store中的拦截器统一处理
    if (error.response?.status !== 401) {
      console.error('API响应错误:', error.response?.status, error.message)
      
      // 添加CORS错误特殊处理
      if (error.message && error.message.includes('Network Error')) {
        console.error('可能存在CORS跨域问题，请检查后端CORS配置是否正确')
      }
    }
    return Promise.reject(error)
  }
)

// 导出apiClient (改为命名导出)
export { apiClient }

// 用户相关API
export const userApi = {
  login: (email: string, password: string) => {
    // 使用URLSearchParams创建x-www-form-urlencoded格式的数据
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    
    // 添加调试日志
    console.log('登录请求数据:', { username: email, password: '***' })
    console.log('登录请求URL:', '/api/v1/users/login')
    console.log('登录请求头:', { 'Content-Type': 'application/x-www-form-urlencoded' })
    
    return apiClient.post('/api/v1/users/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },
  
  register: (userData: UserCreate | Record<string, unknown>) => {
    return apiClient.post('/api/v1/users/register', userData)
  },
  
  getProfile: () => {
    return apiClient.get<User>('/api/v1/users/profile')
  },
  
  updateProfile: (userData: UserUpdate) => {
    return apiClient.put<User>('/api/v1/users/profile', userData)
  },
  
  riskAssessment: (data: any) => {
    return apiClient.post('/api/v1/users/risk-assessment', data)
  }
}

// 健康数据相关API
export const healthApi = {
  getHealthData: (params?: any) => {
    return apiClient.get('/api/v1/health', { params })
  },
  
  addHealthData: (data: any) => {
    return apiClient.post('/api/v1/health', data)
  },
  
  updateHealthData: (id: string, data: any) => {
    return apiClient.put(`/api/v1/health/${id}`, data)
  },
  
  deleteHealthData: (id: string) => {
    return apiClient.delete(`/api/v1/health/${id}`)
  }
}

// 血糖相关API
export const glucoseApi = {
  getGlucoseRecords: (params?: any) => {
    return apiClient.get('/api/v1/glucose', { params })
  },
  
  addGlucoseRecord: (data: any) => {
    console.log('添加血糖记录:', data)
    return apiClient.post('/api/v1/glucose', data)
  },
  
  updateGlucoseRecord: (id: string, data: any) => {
    console.log('更新血糖记录:', id, data)
    return apiClient.put(`/api/v1/glucose/${id}`, data)
  },
  
  deleteGlucoseRecord: (id: string) => {
    return apiClient.delete(`/api/v1/glucose/${id}`)
  },
  
  getStatistics: (period: 'day' | 'week' | 'month' | 'quarter' = 'week') => {
    return apiClient.get<GlucoseStatistics>(`/api/v1/glucose/statistics?period=${period}`)
  },
  
  getRecentGlucoseRecords: (days: number = 7) => {
    return apiClient.get(`/api/v1/glucose/recent`, { params: { days } })
  }
}

// 饮食相关API
export const dietApi = {
  getDietRecords: (params?: any) => {
    return apiClient.get('/api/v1/diet', { params })
  },
  
  addDietRecord: (data: any) => {
    return apiClient.post('/api/v1/diet', data)
  },
  
  updateDietRecord: (id: string, data: any) => {
    return apiClient.put(`/api/v1/diet/${id}`, data)
  },
  
  deleteDietRecord: (id: string) => {
    return apiClient.delete(`/api/v1/diet/${id}`)
  },
  
  getFoodSuggestions: (query: string) => {
    return apiClient.get(`/api/v1/diet/food-suggestions?query=${query}`)
  }
}

// 智能助理相关API
export const assistantApi = {
  sendMessage: (message: string, conversationId?: string) => {
    return apiClient.post('/api/v1/assistant/chat', { 
      message,
      conversation_id: conversationId
    })
  },
  
  getConversationHistory: () => {
    return apiClient.get('/api/v1/assistant/history')
  },
  
  clearConversation: () => {
    return apiClient.delete('/api/v1/assistant/history')
  },
  
  getConversations: () => {
    return apiClient.get('/api/v1/assistant/conversations')
  },
  
  getConversationMessages: (conversationId: string) => {
    return apiClient.get(`/api/v1/assistant/conversations/${conversationId}/messages`)
  },
  
  createConversation: (title: string, initialMessage?: string) => {
    return apiClient.post('/api/v1/assistant/conversations', {
      title,
      initial_message: initialMessage
    })
  },
  
  deleteConversation: (conversationId: string) => {
    return apiClient.delete(`/api/v1/assistant/conversations/${conversationId}`)
  }
}

// 知识库相关API
export const knowledgeApi = {
  searchKnowledge: (query: string) => {
    return apiClient.get(`/api/v1/knowledge/search?query=${query}`)
  },
  
  getKnowledgeById: (id: string) => {
    return apiClient.get(`/api/v1/knowledge/${id}`)
  },
  
  getCategories: () => {
    return apiClient.get('/api/v1/knowledge/categories')
  },
  
  getByCategory: (category: string) => {
    return apiClient.get(`/api/v1/knowledge/category/${category}`)
  }
}

// Ollama大模型API
export const ollamaApi = {
  // 检查Ollama服务健康状态
  checkHealth: () => {
    return apiClient.get('/api/v1/ollama/health')
  },
  
  // 获取可用模型列表
  listModels: () => {
    return apiClient.get('/api/v1/ollama/models')
  },
  
  // 单轮对话生成回复
  generateText: (prompt: string, model?: string, system?: string, temperature?: number, maxTokens?: number) => {
    return apiClient.post('/api/v1/ollama/generate', {
      prompt,
      model,
      system,
      temperature,
      max_tokens: maxTokens
    })
  },
  
  // 多轮对话
  chat: (messages: Array<{role: string, content: string}>, model?: string, system?: string, temperature?: number, maxTokens?: number) => {
    const requestData = {
      messages,
      model,
      system,
      temperature,
      max_tokens: maxTokens
    };
    console.log('发送Ollama聊天请求:', requestData);
    return apiClient.post('/api/v1/ollama/chat', requestData);
  }
}

export default {
  user: userApi,
  health: healthApi,
  glucose: glucoseApi,
  diet: dietApi,
  assistant: assistantApi,
  knowledge: knowledgeApi,
  ollama: ollamaApi
}
