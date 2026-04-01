import axios, { type AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'
import { decryptWithAes, decryptBase64, encryptBase64, encryptWithAes, generateAesKey } from '@/utils/crypto'
import { decrypt, encrypt } from '@/utils/jsencrypt'
import { message } from '@/utils/discrete'

const encryptHeader = 'encrypt-key'
const repeatSubmitKey = 'source-link-last-request'

declare module 'axios' {
  export interface AxiosRequestConfig {
    skipAuth?: boolean
    encrypt?: boolean
    skipRepeatSubmit?: boolean
    rawResponse?: boolean
  }
}

function isEncryptionEnabled() {
  return import.meta.env.VITE_APP_ENCRYPT === 'true'
}

function saveRepeatRecord(config: InternalAxiosRequestConfig) {
  if (config.skipRepeatSubmit || !['post', 'put'].includes(config.method ?? '')) {
    return
  }
  const record = {
    url: config.url,
    data: typeof config.data === 'string' ? config.data : JSON.stringify(config.data ?? {}),
    time: Date.now(),
  }
  const cached = window.sessionStorage.getItem(repeatSubmitKey)
  if (cached) {
    const previous = JSON.parse(cached) as typeof record
    if (previous.url === record.url && previous.data === record.data && record.time - previous.time < 500) {
      throw new Error('数据正在处理中，请勿重复提交')
    }
  }
  window.sessionStorage.setItem(repeatSubmitKey, JSON.stringify(record))
}

const http = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8',
    clientid: import.meta.env.VITE_APP_CLIENT_ID,
  },
})

http.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (!config.skipAuth && authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  config.headers.clientid = import.meta.env.VITE_APP_CLIENT_ID
  saveRepeatRecord(config)

  if (isEncryptionEnabled() && config.encrypt && ['post', 'put'].includes(config.method ?? '')) {
    const aesKey = generateAesKey()
    const rsaKey = encrypt(encryptBase64(aesKey))
    if (rsaKey) {
      config.headers[encryptHeader] = rsaKey
      const payload = typeof config.data === 'string' ? config.data : JSON.stringify(config.data ?? {})
      config.data = encryptWithAes(payload, aesKey)
    }
  }

  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }

  return config
})

http.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.config.rawResponse) {
      return response
    }

    if (isEncryptionEnabled()) {
      const encryptedKey = response.headers[encryptHeader]
      if (encryptedKey && typeof response.data === 'string') {
        const decodedKey = decrypt(encryptedKey)
        if (decodedKey) {
          const aesKey = decryptBase64(decodedKey.toString())
          response.data = JSON.parse(decryptWithAes(response.data, aesKey))
        }
      }
    }

    const data = response.data
    const code = data?.code ?? 200
    if (response.request?.responseType === 'blob' || response.request?.responseType === 'arraybuffer') {
      return data
    }

    if (code === 200) {
      return data
    }

    if (code === 401) {
      const authStore = useAuthStore()
      authStore.clearSession()
      if (router.currentRoute.value.path !== '/login') {
        void router.replace({
          path: '/login',
          query: { redirect: router.currentRoute.value.fullPath },
        })
      }
      message.warning(data?.msg ?? '登录状态已失效，请重新登录')
      return Promise.reject(new Error(data?.msg ?? 'Unauthorized'))
    }

    message.error(data?.msg ?? '请求失败')
    return Promise.reject(new Error(data?.msg ?? 'Request failed'))
  },
  (error: AxiosError) => {
    let messageText = error.message || '请求异常'
    if (messageText.includes('timeout')) {
      messageText = '接口请求超时'
    } else if (messageText.includes('Network Error')) {
      messageText = '后端服务连接失败'
    } else if (messageText.includes('status code')) {
      messageText = `服务返回异常：${messageText.slice(-3)}`
    }
    message.error(messageText)
    return Promise.reject(error)
  },
)

export default http
