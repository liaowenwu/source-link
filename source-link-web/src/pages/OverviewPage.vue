<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NDataTable, NSkeleton } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { Icon } from '@iconify/vue'
import ConsolePage from '@/components/ConsolePage.vue'
import MetricCard from '@/components/MetricCard.vue'
import { listOnlineUsers } from '@/api/modules/monitor'
import { listRoles, listTenants, listUsers } from '@/api/modules/system'
import type { OnlineUserVO } from '@/types/common'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const loading = ref(true)
const onlineRows = ref<OnlineUserVO[]>([])
const stats = reactive({
  users: 0,
  roles: 0,
  tenants: 0,
  online: 0,
})

const columns: DataTableColumns<OnlineUserVO> = [
  { title: '用户名', key: 'userName' },
  { title: '部门', key: 'deptName' },
  { title: '登录 IP', key: 'ipaddr' },
  { title: '浏览器', key: 'browser' },
  {
    title: '登录时间',
    key: 'loginTime',
    render: (row) => formatDateTime(row.loginTime),
  },
]

async function loadDashboard() {
  loading.value = true
  try {
    const [userRes, roleRes, tenantRes, onlineRes] = await Promise.all([
      listUsers({ pageNum: 1, pageSize: 1 }),
      listRoles({ pageNum: 1, pageSize: 1 }),
      listTenants({ pageNum: 1, pageSize: 1 }),
      listOnlineUsers({ pageNum: 1, pageSize: 8 }),
    ])
    stats.users = userRes.total
    stats.roles = roleRes.total
    stats.tenants = tenantRes.total
    stats.online = onlineRes.total
    onlineRows.value = onlineRes.rows
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <ConsolePage
    title="运营总览"
    eyebrow="Source Link"
    description="集中查看平台用户、角色、租户和在线会话状态，快速进入常用系统管理页面。"
  >
    <template #actions>
      <NButton strong secondary @click="loadDashboard">
        <template #icon>
          <Icon icon="solar:restart-bold-duotone" width="18" />
        </template>
        刷新数据
      </NButton>
      <NButton strong secondary type="primary" @click="router.push('/monitor/center')">
        <template #icon>
          <Icon icon="solar:window-frame-bold-duotone" width="18" />
        </template>
        打开监控中心
      </NButton>
    </template>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard title="系统用户" :value="stats.users" note="当前平台已创建的用户账号总数" accent="teal" />
      <MetricCard title="角色数量" :value="stats.roles" note="已配置角色及权限分组数量" accent="slate" />
      <MetricCard title="租户总数" :value="stats.tenants" note="当前接入平台的租户数量" accent="copper" />
      <MetricCard title="在线会话" :value="stats.online" note="当前处于登录中的在线用户数量" accent="teal" />
    </div>

    <div class="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
      <NCard title="最近在线用户" class="rounded-[24px] border-none">
        <NSkeleton v-if="loading" text :repeat="5" />
        <NDataTable v-else :columns="columns" :data="onlineRows" :pagination="false" :bordered="false" />
      </NCard>

      <div class="grid gap-5">
        <NCard title="快捷入口" class="rounded-[24px] border-none">
          <div class="grid gap-3">
            <button
              class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] px-4 py-4 text-left transition hover:border-[#1f6f6e]"
              @click="router.push('/system/users')"
            >
              <div class="text-sm font-semibold text-[color:var(--text-main)]">用户管理</div>
              <div class="mt-1 text-sm text-[color:var(--text-secondary)]">维护用户资料、角色分配、岗位信息和账号状态。</div>
            </button>
            <button
              class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] px-4 py-4 text-left transition hover:border-[#1f6f6e]"
              @click="router.push('/tenant/tenants')"
            >
              <div class="text-sm font-semibold text-[color:var(--text-main)]">租户管理</div>
              <div class="mt-1 text-sm text-[color:var(--text-secondary)]">管理租户资料、账号额度、套餐绑定和到期时间。</div>
            </button>
            <button
              class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] px-4 py-4 text-left transition hover:border-[#1f6f6e]"
              @click="router.push('/monitor/operlog')"
            >
              <div class="text-sm font-semibold text-[color:var(--text-main)]">操作日志</div>
              <div class="mt-1 text-sm text-[color:var(--text-secondary)]">快速查看关键操作记录、接口结果和异常提示。</div>
            </button>
          </div>
        </NCard>

        <NCard title="使用建议" class="rounded-[24px] border-none">
          <div class="space-y-3 text-sm leading-7 text-[color:var(--text-secondary)]">
            <p>建议优先完成角色、菜单、部门、岗位的基础配置，再批量创建用户和租户，后续授权会更顺畅。</p>
            <p>如果登录页验证码不显示或后端报 Redis 连接失败，需要单独检查后端服务、缓存配置和验证码接口返回值。</p>
            <p>当前前端已经统一为明亮风格控制台，系统管理和租户管理入口都可以直接在左侧导航中访问。</p>
          </div>
        </NCard>
      </div>
    </div>
  </ConsolePage>
</template>
