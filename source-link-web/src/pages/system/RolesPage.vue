<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import {
  NButton,
  NCard,
  NCheckbox,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NPopconfirm,
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  NTree,
} from 'naive-ui'
import type { DataTableColumns, FormInst } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { changeRoleStatus, createRole, deleteRole, getRole, listRoles, menuTreeSelect, roleDeptTree, roleMenuTree, updateRole, updateRoleDataScope } from '@/api/modules/system'
import type { RoleForm, RoleVO, TreeOptionNode } from '@/types/common'
import { toNaiveTreeOptions } from '@/utils/tree'
import { message } from '@/utils/discrete'

type TreeKey = string | number

const loading = ref(false)
const visible = ref(false)
const dataScopeVisible = ref(false)
const isEdit = ref(false)
const rows = ref<RoleVO[]>([])
const total = ref(0)
const formRef = ref<FormInst | null>(null)
const dataScopeFormRef = ref<FormInst | null>(null)
const menuTree = ref<TreeOptionNode[]>([])
const deptTree = ref<TreeOptionNode[]>([])
const checkedMenuKeys = ref<TreeKey[]>([])
const checkedDeptKeys = ref<TreeKey[]>([])

const query = reactive({
  pageNum: 1,
  pageSize: 10,
  roleName: '',
  roleKey: '',
})

const form = reactive<RoleForm>({
  roleId: undefined,
  roleName: '',
  roleKey: '',
  roleSort: 1,
  dataScope: '1',
  status: '0',
  remark: '',
  menuCheckStrictly: true,
  deptCheckStrictly: true,
  menuIds: [],
  deptIds: [],
})

const dataScopeForm = reactive({
  roleId: undefined as string | number | undefined,
  roleName: '',
  dataScope: '1',
  deptCheckStrictly: true,
})

const dataScopeOptions = [
  { label: '全部数据权限', value: '1' },
  { label: '自定义数据权限', value: '2' },
  { label: '本部门数据权限', value: '3' },
  { label: '本部门及以下数据权限', value: '4' },
  { label: '仅本人数据权限', value: '5' },
  { label: '本部门及以下或本人数据权限', value: '6' },
]

function resetFormState() {
  Object.assign(form, {
    roleId: undefined,
    roleName: '',
    roleKey: '',
    roleSort: 1,
    dataScope: '1',
    status: '0',
    remark: '',
    menuCheckStrictly: true,
    deptCheckStrictly: true,
    menuIds: [],
    deptIds: [],
  })
  checkedMenuKeys.value = []
}

function resetDataScopeState() {
  Object.assign(dataScopeForm, {
    roleId: undefined,
    roleName: '',
    dataScope: '1',
    deptCheckStrictly: true,
  })
  checkedDeptKeys.value = []
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listRoles(query)
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
    roleName: '',
    roleKey: '',
    pageNum: 1,
  })
  loadTable()
}

async function loadMenuTree() {
  const result = await menuTreeSelect()
  menuTree.value = result.data
}

async function openCreate() {
  isEdit.value = false
  resetFormState()
  await loadMenuTree()
  visible.value = true
}

async function openEdit(row: RoleVO) {
  isEdit.value = true
  resetFormState()
  const [roleRes, menuRes] = await Promise.all([getRole(row.roleId), roleMenuTree(row.roleId)])
  Object.assign(form, roleRes.data)
  menuTree.value = menuRes.data.menus
  checkedMenuKeys.value = menuRes.data.checkedKeys
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  const payload: RoleForm = {
    ...form,
    menuIds: checkedMenuKeys.value,
    deptIds: form.deptIds ?? [],
  }
  if (isEdit.value) {
    await updateRole(payload)
    message.success('角色更新成功')
  } else {
    await createRole(payload)
    message.success('角色创建成功')
  }
  visible.value = false
  await loadTable()
}

async function openDataScope(row: RoleVO) {
  resetDataScopeState()
  const [roleRes, deptRes] = await Promise.all([getRole(row.roleId), roleDeptTree(row.roleId)])
  Object.assign(dataScopeForm, {
    roleId: row.roleId,
    roleName: roleRes.data.roleName,
    dataScope: roleRes.data.dataScope ?? '1',
    deptCheckStrictly: roleRes.data.deptCheckStrictly ?? true,
  })
  deptTree.value = deptRes.data.depts
  checkedDeptKeys.value = deptRes.data.checkedKeys
  dataScopeVisible.value = true
}

async function submitDataScope() {
  await dataScopeFormRef.value?.validate()
  await updateRoleDataScope({
    roleId: dataScopeForm.roleId,
    roleName: '',
    roleKey: '',
    roleSort: 0,
    dataScope: dataScopeForm.dataScope,
    status: '0',
    remark: '',
    menuCheckStrictly: true,
    deptCheckStrictly: dataScopeForm.deptCheckStrictly,
    menuIds: [],
    deptIds: dataScopeForm.dataScope === '2' ? checkedDeptKeys.value : [],
  })
  dataScopeVisible.value = false
  message.success('数据权限更新成功')
  await loadTable()
}

async function handleDelete(row: RoleVO) {
  await deleteRole(row.roleId)
  message.success('角色删除成功')
  await loadTable()
}

async function handleStatus(row: RoleVO) {
  const nextStatus = row.status === '0' ? '1' : '0'
  await changeRoleStatus(row.roleId, nextStatus)
  message.success('状态更新成功')
  await loadTable()
}

function renderDataScopeLabel(value?: string) {
  return dataScopeOptions.find((item) => item.value === value)?.label || '-'
}

function updateMenuKeys(keys: TreeKey[]) {
  checkedMenuKeys.value = keys
}

function updateDeptKeys(keys: TreeKey[]) {
  checkedDeptKeys.value = keys
}

const columns: DataTableColumns<RoleVO> = [
  { title: '角色名称', key: 'roleName', width: 180 },
  { title: '角色标识', key: 'roleKey', width: 180 },
  { title: '排序', key: 'roleSort', width: 80 },
  { title: '数据权限', key: 'dataScope', width: 200, render: (row) => renderDataScopeLabel(row.dataScope) },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status }) },
  { title: '备注', key: 'remark', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 260,
    render: (row) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', strong: true, secondary: true, type: 'info', onClick: () => openDataScope(row) }, { default: () => '数据权限' }),
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => handleStatus(row) }, { default: () => (row.status === '0' ? '停用' : '启用') }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () =>
                h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => `确定删除角色“${row.roleName}”吗？`,
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
  <ConsolePage title="角色管理" eyebrow="系统管理" description="维护角色、菜单权限和数据权限范围，支持按角色快速授权。">
    <template #actions>
      <NButton strong secondary type="primary" @click="openCreate">新增角色</NButton>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.roleName" placeholder="角色名称" clearable class="max-w-[170px]" />
        <NInput v-model:value="query.roleKey" placeholder="角色标识" clearable class="max-w-[170px]" />
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
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑角色' : '新增角色' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="角色名称" path="roleName">
              <NInput v-model:value="form.roleName" />
            </NFormItem>
            <NFormItem label="角色标识" path="roleKey">
              <NInput v-model:value="form.roleKey" />
            </NFormItem>
            <NFormItem label="显示排序" path="roleSort">
              <NInputNumber v-model:value="form.roleSort" :min="1" class="w-full" />
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
            <NFormItem label="菜单联动" class="md:col-span-2">
              <NCheckbox v-model:checked="form.menuCheckStrictly">父子节点联动选择</NCheckbox>
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
              default-expand-all
              :cascade="form.menuCheckStrictly"
              :data="toNaiveTreeOptions(menuTree)"
              :checked-keys="checkedMenuKeys"
              @update:checked-keys="(keys) => updateMenuKeys(keys as TreeKey[])"
            />
          </div>

          <div class="mt-4 flex justify-end gap-3">
            <NButton strong secondary @click="visible = false">取消</NButton>
            <NButton strong secondary type="primary" @click="submitForm">保存</NButton>
          </div>
        </NForm>
      </div>
    </NModal>

    <NModal v-model:show="dataScopeVisible">
      <div class="mx-auto w-[min(920px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">数据权限 - {{ dataScopeForm.roleName }}</h3>
        <NForm ref="dataScopeFormRef" :model="dataScopeForm" label-placement="top">
          <NFormItem label="数据权限范围">
            <NRadioGroup v-model:value="dataScopeForm.dataScope">
              <NSpace vertical>
                <NRadio v-for="item in dataScopeOptions" :key="item.value" :value="item.value">
                  {{ item.label }}
                </NRadio>
              </NSpace>
            </NRadioGroup>
          </NFormItem>

          <NFormItem v-if="dataScopeForm.dataScope === '2'" label="部门联动">
            <NCheckbox v-model:checked="dataScopeForm.deptCheckStrictly">父子节点联动选择</NCheckbox>
          </NFormItem>

          <div v-if="dataScopeForm.dataScope === '2'" class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] p-4">
            <div class="mb-3 text-sm font-semibold text-[color:var(--text-main)]">部门权限</div>
            <NTree
              checkable
              block-line
              default-expand-all
              :cascade="dataScopeForm.deptCheckStrictly"
              :data="toNaiveTreeOptions(deptTree)"
              :checked-keys="checkedDeptKeys"
              @update:checked-keys="(keys) => updateDeptKeys(keys as TreeKey[])"
            />
          </div>

          <div class="mt-4 flex justify-end gap-3">
            <NButton strong secondary @click="dataScopeVisible = false">取消</NButton>
            <NButton strong secondary type="primary" @click="submitDataScope">保存</NButton>
          </div>
        </NForm>
      </div>
    </NModal>
  </ConsolePage>
</template>
