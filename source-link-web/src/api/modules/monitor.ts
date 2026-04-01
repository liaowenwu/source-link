import http from '@/api/http'
import type {
  ApiResult,
  CacheInfoPayload,
  LoginLogVO,
  OnlineUserVO,
  OperLogVO,
  PageQuery,
  PageResult,
} from '@/types/common'

export function listOnlineUsers(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<OnlineUserVO>>('/monitor/online/list', { params })
}

export function forceLogout(tokenId: string) {
  return http.delete<string, ApiResult<null>>(`/monitor/online/${tokenId}`)
}

export function listOperationLogs(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<OperLogVO>>('/monitor/operlog/list', { params })
}

export function deleteOperationLog(operId: string | number) {
  return http.delete<string, ApiResult<null>>(`/monitor/operlog/${operId}`)
}

export function cleanOperationLogs() {
  return http.delete<string, ApiResult<null>>('/monitor/operlog/clean')
}

export function listLoginLogs(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<LoginLogVO>>('/monitor/logininfor/list', { params })
}

export function deleteLoginLog(infoId: string | number) {
  return http.delete<string, ApiResult<null>>(`/monitor/logininfor/${infoId}`)
}

export function cleanLoginLogs() {
  return http.delete<string, ApiResult<null>>('/monitor/logininfor/clean')
}

export function unlockLoginUser(userName: string) {
  return http.get<string, ApiResult<null>>(`/monitor/logininfor/unlock/${userName}`)
}

export function getCacheInfo() {
  return http.get<string, ApiResult<CacheInfoPayload>>('/monitor/cache')
}
