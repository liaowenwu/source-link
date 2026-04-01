import { defineStore } from 'pinia'

const storageKey = 'source-link-theme-mode'

type ThemeMode = 'light' | 'dark'

export const useAppStore = defineStore('app', {
  state: () => ({
    sidebarCollapsed: false,
    themeMode: (window.localStorage.getItem(storageKey) as ThemeMode | null) ?? 'light',
  }),
  getters: {
    isDark: (state) => state.themeMode === 'dark',
  },
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    toggleTheme() {
      this.themeMode = this.isDark ? 'light' : 'dark'
      window.localStorage.setItem(storageKey, this.themeMode)
    },
  },
})
