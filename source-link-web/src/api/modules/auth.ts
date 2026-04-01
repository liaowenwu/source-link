import http from '@/api/http'
import type { ApiResult, CaptchaPayload, TenantListPayload, UserInfoPayload } from '@/types/common'

export interface LoginPayload {
  username: string
  password: string
  code?: string
  uuid?: string
  tenantId?: string
  clientId?: string
  grantType?: string
}

export interface LoginResult {
  access_token: string
  refresh_token?: string
  expire_in?: number
  client_id?: string
}

export function login(payload: LoginPayload) {
  return http.post<string, ApiResult<LoginResult>>('/auth/login', {
    ...payload,
    clientId: payload.clientId ?? import.meta.env.VITE_APP_CLIENT_ID,
    grantType: payload.grantType ?? 'password',
  }, {
    skipAuth: true,
    encrypt: true,
    skipRepeatSubmit: true,
  })
}

export function logout() {
  return http.post<string, ApiResult<null>>('/auth/logout')
}

export function getCaptcha() {
  return http.get<string, ApiResult<CaptchaPayload>>('/auth/code', {
    skipAuth: true,
  })
}

export function getTenantList() {
  return http.get<string, ApiResult<TenantListPayload>>('/auth/tenant/list', {
    skipAuth: true,
  })
}

export function getProfile() {
  return http.get<string, ApiResult<UserInfoPayload>>('/system/user/getInfo')
}
