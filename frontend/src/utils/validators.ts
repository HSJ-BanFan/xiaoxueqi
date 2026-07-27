/**
 * 前端数据验证工具
 * 提供常用的表单验证规则
 */

// 兼容 async-validator 的 rule/value/callback/source 调用签名。
type ValidateRule = (
  rule: any,
  value: any,
  callback: (error?: Error) => void,
  source?: Record<string, unknown>
) => void

/**
 * 必填字段验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const required = (message: string = '此字段为必填项'): ValidateRule => {
  return (rule, value, callback) => {
    if (value === '' || value === null || value === undefined) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 邮箱格式验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const email = (message: string = '请输入有效的邮箱地址'): ValidateRule => {
  return (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }
    
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    if (!emailRegex.test(value)) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 手机号格式验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const phone = (message: string = '请输入有效的手机号'): ValidateRule => {
  return (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }
    
    const phoneRegex = /^1[3456789]\d{9}$/
    if (!phoneRegex.test(value)) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 数值范围验证
 * @param min 最小值
 * @param max 最大值
 * @param message 错误消息
 * @returns 验证规则
 */
export const numberRange = (min: number, max: number, message?: string): ValidateRule => {
  return (rule, value, callback) => {
    if (value === '' || value === null || value === undefined) {
      callback()
      return
    }
    
    const num = Number(value)
    if (isNaN(num)) {
      callback(new Error('请输入有效的数字'))
      return
    }
    
    if (num < min || num > max) {
      callback(new Error(message || `请输入 ${min} 到 ${max} 之间的数值`))
    } else {
      callback()
    }
  }
}

/**
 * 血糖值验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const glucoseValue = (message: string = '请输入有效的血糖值(1.0-30.0 mmol/L)'): ValidateRule => {
  return numberRange(1.0, 30.0, message)
}

/**
 * 密码强度验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const passwordStrength = (message: string = '密码至少包含8个字符，且包含字母和数字'): ValidateRule => {
  return (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }
    
    // 至少8个字符，且包含字母和数字
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/
    if (!passwordRegex.test(value)) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 密码确认验证
 * @param passwordField 密码字段名
 * @param message 错误消息
 * @returns 验证规则
 */
export const confirmPassword = (passwordField: string, message: string = '两次输入的密码不一致'): ValidateRule => {
  return (rule, value, callback, source) => {
    if (value === '' || value === null || value === undefined) {
      callback()
      return
    }
    
    if (value !== source?.[passwordField]) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 用户名格式验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const username = (message: string = '用户名只能包含字母、数字和下划线，长度3-20个字符'): ValidateRule => {
  return (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }
    
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/
    if (!usernameRegex.test(value)) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 日期时间验证
 * @param message 错误消息
 * @returns 验证规则
 */
export const dateTime = (message: string = '请输入有效的日期时间'): ValidateRule => {
  return (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }
    
    const date = new Date(value)
    if (isNaN(date.getTime())) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

/**
 * 创建表单验证规则
 * @param rules 验证规则对象
 * @returns Element Plus表单验证规则对象
 */
export const createFormRules = (rules: Record<string, Array<ValidateRule | object>>) => {
  return rules
}

/**
 * 血糖记录表单验证规则
 */
export const glucoseFormRules = createFormRules({
  value: [
    { required: true, message: '请输入血糖值', trigger: 'blur' },
    { validator: glucoseValue(), trigger: 'blur' }
  ],
  measured_at: [
    { required: true, message: '请选择测量时间', trigger: 'change' },
    { validator: dateTime(), trigger: 'blur' }
  ],
  measurement_time: [
    { required: true, message: '请选择测量类型', trigger: 'change' }
  ],
  measurement_method: [
    { required: true, message: '请选择测量方法', trigger: 'change' }
  ]
})

/**
 * 用户注册表单验证规则
 */
export const registerFormRules = createFormRules({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { validator: username(), trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: email(), trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { validator: passwordStrength(), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: confirmPassword('password'), trigger: 'blur' }
  ],
  full_name: [
    { required: false, message: '请输入姓名', trigger: 'blur' }
  ]
})

export default {
  required,
  email,
  phone,
  numberRange,
  glucoseValue,
  passwordStrength,
  confirmPassword,
  username,
  dateTime,
  createFormRules,
  glucoseFormRules,
  registerFormRules
}
