<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import { NButton, NCard, NDataTable, NInput, NPopconfirm, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import { forceLogout, listOnlineUsers } from '@/api/modules/monitor'
import type { OnlineUserVO } from '@/types/common'
import { formatDateTime } from '@/utils/format'
import { message } from '@/utils/discrete'

const loading = ref(false)
const rows = ref<OnlineUserVO[]>([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 10, userName: '', ipaddr: '' })

async function loadData() {
  loading.value = true
  try {
    const result = await listOnlineUsers(query)
    rows.value = result.rows
    total.value = result.total
  } finally {
    loading.value = false
  }
}

async function handleForceLogout(row: OnlineUserVO) {
  await forceLogout(row.tokenId)
  message.success(`已强制下线 ${row.userName}`)
  await loadData()
}

const columns: DataTableColumns<OnlineUserVO> = [
  { title: '用户', key: 'userName' },
  { title: '部门', key: 'deptName' },
  { title: 'IP', key: 'ipaddr' },
  { title: '登录地点', key: 'loginLocation' },
  { title: '浏览器', key: 'browser' },
  { title: '系统', key: 'os' },
  { title: '登录时间', key: 'loginTime', render: (row) => formatDateTime(row.loginTime) },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
      h(
        NPopconfirm,
        { onPositiveClick: () => handleForceLogout(row) },
        {
          trigger: () => h(NButton, { size: 'small', tertiary: true, type: 'error' }, { default: () => '强退' }),
          default: () => `确认强制 ${row.userName} 下线吗？`,
        },
      ),
  },
]

onMounted(loadData)
</script>

<template>
  <ConsolePage title="在线用户" eyebrow="Monitor" description="直接对接 `/monitor/online/list` 与强退接口，方便快速查看当前在线会话和来源设备。">
    <NCard class="rounded-[24px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <NInput v-model:value="query.userName" placeholder="按用户名筛选" class="max-w-[220px]" clearable />
        <NInput v-model:value="query.ipaddr" placeholder="按 IP 筛选" class="max-w-[220px]" clearable />
        <NSpace>
          <NButton type="primary" @click="loadData">查询</NButton>
          <NButton tertiary @click="Object.assign(query, { userName: '', ipaddr: '', pageNum: 1 }); loadData()">重置</NButton>
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
