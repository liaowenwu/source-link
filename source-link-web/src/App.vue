<script setup lang="ts">
import { computed } from 'vue'
import { NConfigProvider, NDialogProvider, NMessageProvider, NNotificationProvider } from 'naive-ui'
import { adminDarkTheme, themeOverrides } from '@/theme'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const theme = computed(() => (appStore.isDark ? adminDarkTheme : null))
</script>

<template>
  <NConfigProvider :theme="theme" :theme-overrides="themeOverrides">
    <NMessageProvider>
      <NNotificationProvider>
        <NDialogProvider>
          <RouterView />
        </NDialogProvider>
      </NNotificationProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>
