<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NPopconfirm,
  NSelect,
  NSpace,
} from 'naive-ui'
import type { DataTableColumns, FormInst } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  changeTenantStatus,
  createTenant,
  deleteTenant,
  getTenant,
  listTenants,
  selectTenantPackages,
  syncTenantConfig,
  syncTenantDict,
  syncTenantPackage,
  updateTenant,
} from '@/api/modules/system'
import type { TenantForm, TenantPackageVO, TenantVO } from '@/types/common'
import { formatDateTime } from '@/utils/format'
import { message } from '@/utils/discrete'

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const visible = ref(false)
const isEdit = ref(false)
const rows = ref<TenantVO[]>([])
const total = ref(0)
const packageOptions = ref<Array<{ label: string; value: string | number }>>([])

const query = reactive({
  pageNum: 1,
  pageSize: 10,
  contactUserName: '',
  contactPhone: '',
  companyName: '',
})

const form = reactive<TenantForm>({
  id: undefined,
  tenantId: '',
  username: '',
  password: '',
  contactUserName: '',
  contactPhone: '',
  companyName: '',
  licenseNumber: '',
  address: '',
  domain: '',
  intro: '',
  remark: '',
  packageId: '',
  expireTime: '',
  accountCount: 1,
  status: '0',
})

function resetFormState() {
  Object.assign(form, {
    id: undefined,
    tenantId: '',
    username: '',
    password: '',
    contactUserName: '',
    contactPhone: '',
    companyName: '',
    licenseNumber: '',
    address: '',
    domain: '',
    intro: '',
    remark: '',
    packageId: '',
    expireTime: '',
    accountCount: 1,
    status: '0',
  })
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listTenants(query)
    rows.value = result.rows
    total.value = result.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.pageNum = 1
  loadTable()
}

function resetQuery() {
  Object.assign(query, {
    companyName: '',
    contactUserName: '',
    contactPhone: '',
    pageNum: 1,
  })
  loadTable()
}

async function loadPackages() {
  const result = await selectTenantPackages()
  packageOptions.value = result.data.map((item: TenantPackageVO) => ({ label: item.packageName, value: item.packageId }))
}

async function openCreate() {
  isEdit.value = false
  resetFormState()
  await loadPackages()
  visible.value = true
}

async function openEdit(row: TenantVO) {
  isEdit.value = true
  resetFormState()
  await loadPackages()
  const result = await getTenant(row.id)
  Object.assign(form, result.data)
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  if (isEdit.value) {
    await updateTenant(form)
    message.success('租户更新成功')
  } else {
    await createTenant(form)
    message.success('租户创建成功')
  }
  visible.value = false
  await loadTable()
}

async function handleDelete(row: TenantVO) {
  await deleteTenant(row.id)
  message.success('租户删除成功')
  await loadTable()
}

async function handleStatus(row: TenantVO) {
  const nextStatus = row.status === '0' ? '1' : '0'
  await changeTenantStatus(row.id, row.tenantId, nextStatus)
  message.success('状态更新成功')
  await loadTable()
}

async function handleSyncPackage(row: TenantVO) {
  if (!row.packageId) {
    message.warning('请先为租户分配套餐')
    return
  }
  await syncTenantPackage(row.tenantId, row.packageId)
  message.success('租户套餐同步成功')
}

async function handleSyncDict() {
  await syncTenantDict()
  message.success('租户字典同步成功')
}

async function handleSyncConfig() {
  await syncTenantConfig()
  message.success('租户参数同步成功')
}

const columns: DataTableColumns<TenantVO> = [
  { title: '租户编号', key: 'tenantId', width: 120 },
  { title: '企业名称', key: 'companyName', width: 180 },
  { title: '联系人', key: 'contactUserName', width: 120 },
  { title: '手机号', key: 'contactPhone', width: 150 },
  { title: '账号额度', key: 'accountCount', width: 100 },
  {
    title: '到期时间',
    key: 'expireTime',
    width: 180,
    render: (row) => formatDateTime(row.expireTime),
  },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status }) },
  {
    title: '操作',
    key: 'actions',
    width: 320,
    render: (row) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => handleStatus(row) }, { default: () => (row.status === '0' ? '停用' : '启用') }),
          h(NButton, { size: 'small', strong: true, secondary: true, type: 'info', onClick: () => handleSyncPackage(row) }, { default: () => '同步套餐' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () =>
                h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => `确定删除租户“${row.companyName}”吗？`,
            },
          ),
        ],
      }),
  },
]

onMounted(async () => {
  await Promise.all([loadTable(), loadPackages()])
})
</script>

<template>
  <ConsolePage title="租户管理" eyebrow="租户中心" description="维护租户资料、账号额度、套餐绑定和到期时间，支持同步租户参数与字典。">
    <template #actions>
      <NButton strong secondary type="info" @click="handleSyncDict">同步字典</NButton>
      <NButton strong secondary type="info" @click="handleSyncConfig">同步参数</NButton>
      <NButton strong secondary type="primary" @click="openCreate">新增租户</NButton>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.companyName" placeholder="企业名称" clearable class="max-w-[170px]" />
        <NInput v-model:value="query.contactUserName" placeholder="联系人" clearable class="max-w-[170px]" />
        <NInput v-model:value="query.contactPhone" placeholder="手机号" clearable class="max-w-[170px]" />
        <NSpace>
          <NButton strong secondary type="primary" @click="handleSearch">搜索</NButton>
          <NButton strong secondary @click="resetQuery">重置</NButton>
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
          onUpdatePage: (page: number) => {
            query.pageNum = page
            loadTable()
          },
        }"
        :bordered="false"
      />
    </NCard>

    <NModal v-model:show="visible">
      <div class="mx-auto w-[min(980px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑租户' : '新增租户' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="租户编号" path="tenantId">
              <NInput :value="String(form.tenantId ?? '')" :disabled="isEdit" @update:value="(value) => (form.tenantId = value)" />
            </NFormItem>
            <NFormItem label="登录账号" path="username">
              <NInput v-model:value="form.username" />
            </NFormItem>
            <NFormItem v-if="!isEdit" label="登录密码" path="password">
              <NInput v-model:value="form.password" type="password" show-password-on="click" />
            </NFormItem>
            <NFormItem label="联系人" path="contactUserName">
              <NInput v-model:value="form.contactUserName" />
            </NFormItem>
            <NFormItem label="手机号" path="contactPhone">
              <NInput v-model:value="form.contactPhone" />
            </NFormItem>
            <NFormItem label="企业名称" path="companyName">
              <NInput v-model:value="form.companyName" />
            </NFormItem>
            <NFormItem label="统一社会信用代码">
              <NInput v-model:value="form.licenseNumber" />
            </NFormItem>
            <NFormItem label="租户套餐" path="packageId">
              <NSelect v-model:value="form.packageId" :options="packageOptions" />
            </NFormItem>
            <NFormItem label="到期时间" path="expireTime">
              <NInput v-model:value="form.expireTime" placeholder="YYYY-MM-DD HH:mm:ss" />
            </NFormItem>
            <NFormItem label="账号额度" path="accountCount">
              <NInputNumber v-model:value="form.accountCount" :min="1" class="w-full" />
            </NFormItem>
            <NFormItem label="状态" path="status">
              <NSelect
                v-model:value="form.status"
                :options="[
                  { label: '启用', value: '0' },
                  { label: '停用', value: '1' },
                ]"
              />
            </NFormItem>
            <NFormItem label="域名" class="md:col-span-2">
              <NInput v-model:value="form.domain" />
            </NFormItem>
            <NFormItem label="地址" class="md:col-span-2">
              <NInput v-model:value="form.address" />
            </NFormItem>
            <NFormItem label="租户简介" class="md:col-span-2">
              <NInput v-model:value="form.intro" type="textarea" />
            </NFormItem>
            <NFormItem label="备注" class="md:col-span-2">
              <NInput v-model:value="form.remark" type="textarea" />
            </NFormItem>
          </div>
          <div class="mt-4 flex justify-end gap-3">
            <NButton strong secondary @click="visible = false">取消</NButton>
            <NButton strong secondary type="primary" @click="submitForm">保存</NButton>
          </div>
        </NForm>
      </div>
    </NModal>
  </ConsolePage>
</template>
