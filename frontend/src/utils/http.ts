import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

interface ApiErrorPayload {
  detail?: unknown
}

// 错误消息配置
const ERROR_MESSAGES = {
  network: '网络连接错误，请检查您的网络连接',
  timeout: '请求超时，请稍后重试',
  unauthorized: '登录已过期，请重新登录',
  forbidden: '您没有权限执行此操作',
  notFound: '请求的资源不存在',
  serverError: '服务器错误，请稍后重试',
  default: '请求失败，请稍后重试'
}

// 创建axios实例
const axiosInstance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000,
  withCredentials: true
})

// 请求拦截器
axiosInstance.interceptors.request.use(
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

/**
 * 解析验证错误详情
 * @param detail 错误详情对象
 * @returns 格式化的错误消息
 */
const parseValidationError = (detail: any): string => {
  if (!detail) return ERROR_MESSAGES.default
  
  // 处理数组形式的验证错误
  if (Array.isArray(detail)) {
    return detail.map(err => {
      if (err.loc && err.msg) {
        // 去除 body 前缀，使错误消息更友好
        const field = err.loc.filter((item: string) => item !== 'body').join('.')
        return `${field}: ${err.msg}`
      }
      return err.msg || JSON.stringify(err)
    }).join('; ')
  }
  
  // 处理字符串形式的错误
  if (typeof detail === 'string') {
    return detail
  }
  
  // 处理对象形式的错误
  if (typeof detail === 'object') {
    return Object.entries(detail)
      .map(([key, value]) => `${key}: ${value}`)
      .join('; ')
  }
  
  return JSON.stringify(detail)
}

/**
 * 处理API错误
 * @param error Axios错误对象
 * @returns 格式化的错误信息
 */
const handleApiError = (error: AxiosError<ApiErrorPayload>): string => {
  if (!error.response) {
    // 网络错误
    if (error.message.includes('Network Error')) {
      console.error('网络连接错误:', error.message)
      return ERROR_MESSAGES.network
    }
    
    // 超时错误
    if (error.message.includes('timeout')) {
      console.error('请求超时:', error.message)
      return ERROR_MESSAGES.timeout
    }
    
    return ERROR_MESSAGES.default
  }
  
  const { status, data } = error.response
  
  // 根据状态码处理错误
  switch (status) {
    case 400: // 请求错误
      if (data && data.detail) {
        return `请求参数错误: ${parseValidationError(data.detail)}`
      }
      return '请求参数错误'
    
    case 401: // 未授权
      return ERROR_MESSAGES.unauthorized
    
    case 403: // 禁止访问
      return ERROR_MESSAGES.forbidden
    
    case 404: // 资源不存在
      return ERROR_MESSAGES.notFound
    
    case 422: // 数据验证错误
      if (data && data.detail) {
        return `数据验证失败: ${parseValidationError(data.detail)}`
      }
      return '数据验证失败'
    
    case 500: // 服务器错误
    case 502: // 网关错误
    case 503: // 服务不可用
    case 504: // 网关超时
      return ERROR_MESSAGES.serverError
    
    default:
      return `请求失败(${status}): ${data?.detail ? parseValidationError(data.detail) : ERROR_MESSAGES.default}`
  }
}

// 响应拦截器
axiosInstance.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 获取错误信息
    const errorMessage = handleApiError(error)
    
    // 控制台输出详细错误
    console.error('API响应错误:', {
      status: error.response?.status,
      url: error.config?.url,
      message: errorMessage,
      data: error.response?.data
    })
    
    // 对于401错误，不显示消息，由路由守卫处理
    if (error.response?.status !== 401) {
      // 显示错误消息
      ElMessage.error(errorMessage)
      
      // 特殊处理CORS错误
      if (error.message && error.message.includes('Network Error')) {
        console.error('可能存在CORS跨域问题，请检查后端CORS配置是否正确')
        ElMessage.error('可能存在CORS跨域问题，请检查后端CORS配置是否正确')
      }
    }
    
    return Promise.reject(error)
  }
)

// 封装请求方法
export const http = {
  request<T = any>(config: AxiosRequestConfig): Promise<T> {
    return new Promise((resolve, reject) => {
      axiosInstance
        .request<any, AxiosResponse<T>>(config)
        .then(response => resolve(response.data))
        .catch(error => reject(error))
    })
  },

  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, url, method: 'get' })
  },

  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, url, method: 'post', data })
  },

  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, url, method: 'put', data })
  },

  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, url, method: 'delete' })
  }
}

export default http
