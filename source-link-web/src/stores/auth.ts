import { defineStore } from 'pinia'
import { getProfile, login as loginApi, logout as logoutApi, type LoginPayload } from '@/api/modules/auth'
import type { UserInfoPayload } from '@/types/common'

const tokenKey = 'source-link-access-token'
const profileKey = 'source-link-profile'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: window.localStorage.getItem(tokenKey) ?? '',
    profile: (JSON.parse(window.localStorage.getItem(profileKey) ?? 'null') as UserInfoPayload | null),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    userName: (state) => state.profile?.user?.nickName || state.profile?.user?.userName || '控制台用户',
  },
  actions: {
    setToken(token: string) {
      this.token = token
      window.localStorage.setItem(tokenKey, token)
    },
    setProfile(profile: UserInfoPayload) {
      this.profile = profile
      window.localStorage.setItem(profileKey, JSON.stringify(profile))
    },
    clearSession() {
      this.token = ''
      this.profile = null
      window.localStorage.removeItem(tokenKey)
      window.localStorage.removeItem(profileKey)
    },
    async login(payload: LoginPayload) {
      const result = await loginApi(payload)
      this.setToken(result.data.access_token)
      await this.refreshProfile()
    },
    async refreshProfile() {
      const result = await getProfile()
      this.setProfile(result.data)
      return result.data
    },
    async logout() {
      try {
        if (this.token) {
          await logoutApi()
        }
      } finally {
        this.clearSession()
      }
    },
  },
})
