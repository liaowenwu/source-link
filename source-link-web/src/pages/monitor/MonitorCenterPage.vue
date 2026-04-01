<script setup lang="ts">
import { NButton, NCard } from 'naive-ui'
import { Icon } from '@iconify/vue'
import ConsolePage from '@/components/ConsolePage.vue'

const monitorUrl = import.meta.env.VITE_APP_MONITOR_ADMIN
</script>

<template>
  <ConsolePage title="监控中心" eyebrow="Spring Boot Admin" description="这里保留了独立的监控入口，用来承接 `source-link-monitor` 服务。你可以直接在新控制台里跳转，也可以在独立标签页查看。">
    <NCard class="rounded-[24px] border-none">
      <div class="grid gap-5 xl:grid-cols-[0.55fr_1.45fr]">
        <div class="space-y-4">
          <div class="rounded-[24px] border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] p-5">
            <div class="text-xs uppercase tracking-[0.28em] text-[color:var(--text-muted)]">Monitor Admin</div>
            <h3 class="mt-3 text-2xl font-semibold tracking-tight text-[color:var(--text-main)]">服务监控入口</h3>
            <p class="mt-3 text-sm leading-7 text-[color:var(--text-secondary)]">
              Spring Boot Admin 独立运行在 `source-link-monitor` 模块，用于观察后端应用实例、健康状态和 Actuator 指标。
            </p>
            <div class="mt-5 flex flex-wrap gap-3">
              <NButton type="primary" tag="a" :href="monitorUrl" target="_blank">
                <template #icon><Icon icon="solar:square-top-down-bold-duotone" width="18" /></template>
                新窗口打开
              </NButton>
            </div>
          </div>
        </div>

        <div class="overflow-hidden rounded-[24px] border border-[color:var(--panel-border)] bg-white">
          <iframe :src="monitorUrl" title="monitor" class="h-[760px] w-full border-0" />
        </div>
      </div>
    </NCard>
  </ConsolePage>
</template>
