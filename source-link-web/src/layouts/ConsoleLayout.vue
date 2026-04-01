<script setup lang="ts">
import { computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NLayout, NLayoutContent, NLayoutHeader, NLayoutSider, NMenu, NTag } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { navItems } from '@/config/navigation'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const appStore = useAppStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const monitorAdminUrl = import.meta.env.VITE_APP_MONITOR_ADMIN || '#'

const groupedNav = computed(() => {
  const groups = new Map<string, typeof navItems>()
  navItems.forEach((item) => {
    const current = groups.get(item.group) ?? []
    current.push(item)
    groups.set(item.group, current)
  })

  return Array.from(groups.entries()).map(([group, items]) => ({
    label: group,
    key: group,
    type: 'group',
    children: items.map((item) => ({
      label: item.label,
      key: item.path,
      icon: () => h(Icon, { icon: item.icon, width: 18 }),
    })),
  }))
})

const activeKey = computed(() => route.path)
const currentNav = computed(() => navItems.find((item) => item.path === route.path))
const currentGroup = computed(() => currentNav.value?.group || '总览')
const currentTitle = computed(() => currentNav.value?.label || '系统控制台')
const currentDept = computed(() => authStore.profile?.user?.deptName || '平台管理部')

async function handleLogout() {
  await authStore.logout()
  await router.replace('/login')
}
</script>

<template>
  <NLayout class="app-shell bg-[color:var(--canvas)] text-[color:var(--text-main)]">
    <NLayout has-sider class="h-screen overflow-hidden bg-transparent">
      <NLayoutSider
        bordered
        collapse-mode="width"
        :collapsed-width="76"
        :width="270"
        :collapsed="appStore.sidebarCollapsed"
        class="border-r border-[color:var(--panel-border)] bg-[color:var(--panel)]"
      >
        <div class="flex h-full flex-col">
          <div class="border-b border-[color:var(--panel-border)] px-4 py-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-[color:var(--brand-500)] text-white shadow-[0_18px_40px_rgba(26,115,232,0.28)]">
                <Icon icon="solar:radar-2-bold-duotone" width="22" />
              </div>
              <div v-if="!appStore.sidebarCollapsed" class="space-y-1">
                <div class="text-[11px] uppercase tracking-[0.24em] text-[color:var(--text-muted)]">Source Link</div>
                <div class="text-base font-semibold tracking-tight text-[color:var(--text-main)]">后台管理平台</div>
              </div>
            </div>
          </div>

          <div class="min-h-0 flex-1 px-2 py-3">
            <NMenu
              :value="activeKey"
              :collapsed="appStore.sidebarCollapsed"
              :collapsed-width="76"
              :collapsed-icon-size="20"
              :options="groupedNav"
              @update:value="(key) => router.push(String(key))"
            />
          </div>
        </div>
      </NLayoutSider>

      <NLayout class="bg-transparent">
        <NLayoutHeader bordered class="border-b border-[color:var(--panel-border)] bg-[color:var(--panel)] px-5 py-3.5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs uppercase tracking-[0.22em] text-[color:var(--text-muted)]">{{ currentGroup }}</p>
              <h2 class="truncate text-xl font-semibold text-[color:var(--text-main)]">{{ currentTitle }}</h2>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <div class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] px-3 py-2">
                <div class="flex items-center gap-2">
                  <div class="min-w-0 text-right">
                    <div class="max-w-[180px] truncate text-sm font-semibold text-[color:var(--text-main)]">{{ authStore.userName }}</div>
                    <div class="max-w-[180px] truncate text-xs text-[color:var(--text-muted)]">{{ currentDept }}</div>
                  </div>
                  <NTag size="small" round type="success">在线</NTag>
                </div>
              </div>

              <NButton strong secondary @click="appStore.toggleSidebar">
                <template #icon>
                  <Icon icon="solar:sidebar-minimalistic-bold-duotone" width="17" />
                </template>
                菜单
              </NButton>

              <NButton strong secondary @click="appStore.toggleTheme">
                <template #icon>
                  <Icon :icon="appStore.isDark ? 'solar:sun-2-bold-duotone' : 'solar:moon-bold-duotone'" width="17" />
                </template>
                {{ appStore.isDark ? '浅色' : '深色' }}
              </NButton>

              <NButton strong secondary tag="a" :href="monitorAdminUrl" target="_blank">
                <template #icon>
                  <Icon icon="solar:square-top-down-bold-duotone" width="17" />
                </template>
                监控
              </NButton>

              <NButton strong secondary type="error" @click="handleLogout">
                <template #icon>
                  <Icon icon="solar:logout-3-bold-duotone" width="17" />
                </template>
                退出登录
              </NButton>
            </div>
          </div>
        </NLayoutHeader>

        <NLayoutContent class="app-main overflow-hidden bg-transparent">
          <div class="app-scroll h-full overflow-auto px-5 py-5">
            <RouterView />
          </div>
        </NLayoutContent>
      </NLayout>
    </NLayout>
  </NLayout>
</template>
