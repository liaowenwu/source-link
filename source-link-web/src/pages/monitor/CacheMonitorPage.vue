<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NCard, NDataTable, NEmpty, NSkeleton } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import MetricCard from '@/components/MetricCard.vue'
import { getCacheInfo } from '@/api/modules/monitor'

const loading = ref(true)
const dbSize = ref(0)
const infoRows = ref<Array<{ key: string; value: string }>>([])
const commandRows = ref<Array<{ name: string; value: string }>>([])

const infoColumns: DataTableColumns<{ key: string; value: string }> = [
  { title: '指标', key: 'key' },
  { title: '值', key: 'value' },
]

const commandColumns: DataTableColumns<{ name: string; value: string }> = [
  { title: '命令', key: 'name' },
  { title: '调用次数', key: 'value' },
]

async function loadCache() {
  loading.value = true
  try {
    const result = await getCacheInfo()
    dbSize.value = result.data.dbSize
    infoRows.value = Object.entries(result.data.info).map(([key, value]) => ({ key, value }))
    commandRows.value = result.data.commandStats
  } finally {
    loading.value = false
  }
}

onMounted(loadCache)
</script>

<template>
  <ConsolePage title="缓存监控" eyebrow="Monitor" description="当前后端迁移出的缓存监控接口提供 Redis 基础信息、库大小和命令统计，这里按新的控制台视觉重新组织展示。">
    <div class="grid gap-4 md:grid-cols-3">
      <MetricCard title="DB Size" :value="dbSize" note="Redis 当前库记录规模" accent="teal" />
      <MetricCard title="命令统计" :value="commandRows.length" note="已返回的命令项数量" accent="copper" />
      <MetricCard title="基础指标" :value="infoRows.length" note="Redis info 已解析键值项数量" accent="slate" />
    </div>

    <div class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <NCard title="命令调用热区" class="rounded-[24px] border-none">
        <NSkeleton v-if="loading" text :repeat="8" />
        <NEmpty v-else-if="commandRows.length === 0" description="暂无命令统计数据" />
        <NDataTable v-else :columns="commandColumns" :data="commandRows" :pagination="false" :bordered="false" />
      </NCard>

      <NCard title="Redis Info" class="rounded-[24px] border-none">
        <NSkeleton v-if="loading" text :repeat="10" />
        <NDataTable v-else :columns="infoColumns" :data="infoRows" :pagination="{ pageSize: 12 }" :bordered="false" />
      </NCard>
    </div>
  </ConsolePage>
</template>
