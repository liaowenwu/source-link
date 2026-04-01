<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import { NButton, NCard, NDataTable, NForm, NFormItem, NInput, NModal, NPopconfirm, NSelect, NSpace, NTree } from 'naive-ui'
import type { DataTableColumns, FormInst } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  changeTenantPackageStatus,
  createTenantPackage,
  deleteTenantPackage,
  getTenantPackage,
  listTenantPackages,
  menuTreeSelect,
  tenantPackageMenuTree,
  updateTenantPackage,
} from '@/api/modules/system'
import type { MenuTreePayload, TenantPackageForm, TenantPackageVO, TreeOptionNode } from '@/types/common'
import { toNaiveTreeOptions } from '@/utils/tree'
import { message } from '@/utils/discrete'

type TreeKey = string | number

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const visible = ref(false)
const isEdit = ref(false)
const rows = ref<TenantPackageVO[]>([])
const total = ref(0)
const treeOptions = ref<TreeOptionNode[]>([])
const checkedKeys = ref<TreeKey[]>([])

const query = reactive({
  pageNum: 1,
  pageSize: 10,
  packageName: '',
})

const form = reactive<TenantPackageForm>({
  packageId: undefined,
  packageName: '',
  menuIds: [],
  remark: '',
  menuCheckStrictly: true,
  status: '0',
})

function resetFormState() {
  Object.assign(form, {
    packageId: undefined,
    packageName: '',
    menuIds: [],
    remark: '',
    menuCheckStrictly: true,
    status: '0',
  })
  checkedKeys.value = []
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listTenantPackages(query)
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
    packageName: '',
    pageNum: 1,
  })
  loadTable()
}

async function loadMenuTree() {
  const result = await menuTreeSelect()
  treeOptions.value = result.data
}

async function openCreate() {
  isEdit.value = false
  resetFormState()
  await loadMenuTree()
  visible.value = true
}

async function openEdit(row: TenantPackageVO) {
  isEdit.value = true
  resetFormState()
  await loadMenuTree()
  const result = await getTenantPackage(row.packageId)
  Object.assign(form, result.data, { menuIds: [] })
  const treeRes: MenuTreePayload = (await tenantPackageMenuTree(row.packageId)).data
  checkedKeys.value = treeRes.checkedKeys
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  const payload = {
    ...form,
    menuIds: checkedKeys.value,
  }
  if (isEdit.value) {
    await updateTenantPackage(payload)
    message.success('租户套餐更新成功')
  } else {
    await createTenantPackage(payload)
    message.success('租户套餐创建成功')
  }
  visible.value = false
  await loadTable()
}

async function handleDelete(row: TenantPackageVO) {
  await deleteTenantPackage(row.packageId)
  message.success('租户套餐删除成功')
  await loadTable()
}

async function handleStatus(row: TenantPackageVO) {
  const nextStatus = row.status === '0' ? '1' : '0'
  await changeTenantPackageStatus(row.packageId, nextStatus)
  message.success('状态更新成功')
  await loadTable()
}

function updateCheckedKeys(keys: TreeKey[]) {
  checkedKeys.value = keys
}

const columns: DataTableColumns<TenantPackageVO> = [
  { title: '套餐名称', key: 'packageName', width: 180 },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status || '0' }) },
  { title: '备注', key: 'remark', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    render: (row) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => handleStatus(row) }, { default: () => (row.status === '0' ? '停用' : '启用') }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () =>
                h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => `确定删除套餐“${row.packageName}”吗？`,
            },
          ),
        ],
      }),
  },
]

onMounted(async () => {
  await Promise.all([loadTable(), loadMenuTree()])
})
</script>

<template>
  <ConsolePage title="租户套餐" eyebrow="租户中心" description="维护租户套餐和菜单权限绑定关系，支持按套餐快速授权。">
    <template #actions>
      <NButton strong secondary type="primary" @click="openCreate">新增套餐</NButton>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.packageName" placeholder="套餐名称" clearable class="max-w-[170px]" />
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
      <div class="mx-auto w-[min(960px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑套餐' : '新增套餐' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="套餐名称" path="packageName">
              <NInput v-model:value="form.packageName" />
            </NFormItem>
            <NFormItem label="状态">
              <NSelect
                v-model:value="form.status"
                :options="[
                  { label: '启用', value: '0' },
                  { label: '停用', value: '1' },
                ]"
              />
            </NFormItem>
            <NFormItem label="备注" class="md:col-span-2">
              <NInput v-model:value="form.remark" type="textarea" />
            </NFormItem>
          </div>

          <div class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] p-4">
            <div class="mb-3 text-sm font-semibold text-[color:var(--text-main)]">菜单权限</div>
            <NTree
              checkable
              block-line
              cascade
              default-expand-all
              :data="toNaiveTreeOptions(treeOptions)"
              :checked-keys="checkedKeys"
              @update:checked-keys="(keys) => updateCheckedKeys(keys as TreeKey[])"
            />
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
