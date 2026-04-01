<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import { NButton, NCard, NDataTable, NInput, NModal, NPopconfirm, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import { cleanOperationLogs, deleteOperationLog, listOperationLogs } from '@/api/modules/monitor'
import type { OperLogVO } from '@/types/common'
import { formatDateTime } from '@/utils/format'
import { message } from '@/utils/discrete'

const loading = ref(false)
const rows = ref<OperLogVO[]>([])
const total = ref(0)
const detailVisible = ref(false)
const currentRow = ref<OperLogVO | null>(null)
const query = reactive({ pageNum: 1, pageSize: 10, title: '', operName: '' })

async function loadData() {
  loading.value = true
  try {
    const result = await listOperationLogs(query)
    rows.value = result.rows
    total.value = result.total
  } finally {
    loading.value = false
  }
}

async function handleDelete(row: OperLogVO) {
  await deleteOperationLog(row.operId)
  message.success('日志删除成功')
  await loadData()
}

async function handleClean() {
  await cleanOperationLogs()
  message.success('日志清理成功')
  await loadData()
}

const columns: DataTableColumns<OperLogVO> = [
  { title: '模块名称', key: 'title' },
  { title: '操作人', key: 'operName' },
  { title: 'IP', key: 'operIp' },
  { title: '状态', key: 'status', render: (row) => (row.status === 0 ? '成功' : '失败') },
  { title: '耗时(ms)', key: 'costTime' },
  { title: '操作时间', key: 'operTime', render: (row) => formatDateTime(row.operTime) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h(NSpace, null, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => { currentRow.value = row; detailVisible.value = true } }, { default: () => '详情' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () => h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => '确定删除这条操作日志吗？',
            },
          ),
        ],
      }),
  },
]

onMounted(loadData)
</script>

<template>
  <ConsolePage title="操作日志" eyebrow="系统监控" description="查询、查看并清理系统操作日志。">
    <template #actions>
      <NPopconfirm @positive-click="handleClean">
        <template #trigger>
          <NButton strong secondary type="error">清空日志</NButton>
        </template>
        确定清空全部操作日志吗？
      </NPopconfirm>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.title" placeholder="模块名称" class="max-w-[170px]" clearable />
        <NInput v-model:value="query.operName" placeholder="操作人" class="max-w-[170px]" clearable />
        <NSpace>
          <NButton strong secondary type="primary" @click="loadData">搜索</NButton>
          <NButton strong secondary @click="Object.assign(query, { title: '', operName: '', pageNum: 1 }); loadData()">重置</NButton>
        </NSpace>
      </div>
      <NDataTable
        :columns="columns"
        :data="rows"
        :loading="loading"
        :pagination="{
          page: query.pageNum,
          pageSize: query.pageSize,
          itemCount: total,
          onUpdatePage: (page: number) => { query.pageNum = page; loadData() },
        }"
        :bordered="false"
      />
    </NCard>

    <NModal v-model:show="detailVisible">
      <div class="mx-auto w-[min(760px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-3 text-lg font-semibold">日志详情</h3>
        <pre class="overflow-auto rounded-2xl bg-[color:var(--panel-soft)] p-4 text-xs leading-6 text-[color:var(--text-main)]">{{ JSON.stringify(currentRow, null, 2) }}</pre>
      </div>
    </NModal>
  </ConsolePage>
</template>
