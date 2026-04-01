<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import { NButton, NCard, NDataTable, NInput, NPopconfirm, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import { cleanLoginLogs, deleteLoginLog, listLoginLogs, unlockLoginUser } from '@/api/modules/monitor'
import type { LoginLogVO } from '@/types/common'
import { formatDateTime } from '@/utils/format'
import { message } from '@/utils/discrete'

const loading = ref(false)
const rows = ref<LoginLogVO[]>([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 10, userName: '', ipaddr: '', status: '' })

async function loadData() {
  loading.value = true
  try {
    const result = await listLoginLogs(query)
    rows.value = result.rows
    total.value = result.total
  } finally {
    loading.value = false
  }
}

async function handleDelete(row: LoginLogVO) {
  await deleteLoginLog(row.infoId)
  message.success('登录日志已删除')
  await loadData()
}

async function handleUnlock(row: LoginLogVO) {
  await unlockLoginUser(row.userName)
  message.success(`已解除 ${row.userName} 的登录锁定`)
}

async function handleClean() {
  await cleanLoginLogs()
  message.success('登录日志已清空')
  await loadData()
}

const columns: DataTableColumns<LoginLogVO> = [
  { title: '用户名', key: 'userName' },
  { title: 'IP', key: 'ipaddr' },
  { title: '地点', key: 'loginLocation' },
  { title: '浏览器', key: 'browser' },
  { title: '结果', key: 'status', render: (row) => (row.status === '0' ? '成功' : '失败') },
  { title: '消息', key: 'msg' },
  { title: '时间', key: 'loginTime', render: (row) => formatDateTime(row.loginTime) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h(NSpace, null, {
        default: () => [
          h(NButton, { size: 'small', tertiary: true, onClick: () => handleUnlock(row) }, { default: () => '解锁' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () => h(NButton, { size: 'small', tertiary: true, type: 'error' }, { default: () => '删除' }),
              default: () => '确认删除该日志吗？',
            },
          ),
        ],
      }),
  },
]

onMounted(loadData)
</script>

<template>
  <ConsolePage title="登录日志" eyebrow="Monitor" description="用于排查登录失败、验证码异常与账户锁定，和新的登录加密链路联调时也很有帮助。">
    <template #actions>
      <NPopconfirm @positive-click="handleClean">
        <template #trigger>
          <NButton tertiary type="error">清空日志</NButton>
        </template>
        确认清空全部登录日志吗？
      </NPopconfirm>
    </template>

    <NCard class="rounded-[24px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <NInput v-model:value="query.userName" placeholder="按用户名筛选" class="max-w-[220px]" clearable />
        <NInput v-model:value="query.ipaddr" placeholder="按 IP 筛选" class="max-w-[220px]" clearable />
        <NSpace>
          <NButton type="primary" @click="loadData">查询</NButton>
          <NButton tertiary @click="Object.assign(query, { userName: '', ipaddr: '', status: '', pageNum: 1 }); loadData()">重置</NButton>
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
  </ConsolePage>
</template>
