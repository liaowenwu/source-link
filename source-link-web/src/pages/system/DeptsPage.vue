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
  NTreeSelect,
} from 'naive-ui'
import type { DataTableColumns, FormInst } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { createDept, deleteDept, getDept, listDeptExcludeChild, listDepts, updateDept } from '@/api/modules/system'
import type { DeptForm, DeptVO, TreeOptionNode } from '@/types/common'
import { toNaiveTreeOptions } from '@/utils/tree'
import { message } from '@/utils/discrete'

const loading = ref(false)
const visible = ref(false)
const isEdit = ref(false)
const rows = ref<DeptVO[]>([])
const parentOptions = ref<TreeOptionNode[]>([])
const formRef = ref<FormInst | null>(null)

const query = reactive({
  deptName: '',
  leader: '',
})

const form = reactive<DeptForm>({
  deptId: undefined,
  parentId: 0,
  deptName: '',
  deptCategory: '',
  orderNum: 0,
  leader: '',
  phone: '',
  email: '',
  status: '0',
})

function resetFormState() {
  Object.assign(form, {
    deptId: undefined,
    parentId: 0,
    deptName: '',
    deptCategory: '',
    orderNum: 0,
    leader: '',
    phone: '',
    email: '',
    status: '0',
  })
}

function convertDeptNode(node: DeptVO): TreeOptionNode {
  return {
    id: node.deptId,
    label: node.deptName,
    children: (node.children ?? []).map((item) => convertDeptNode(item)),
  }
}

function withRootNode(nodes: DeptVO[]): TreeOptionNode[] {
  return [
    {
      id: 0,
      label: '顶级部门',
      children: nodes.map((item) => convertDeptNode(item)),
    },
  ]
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listDepts(query)
    rows.value = result.data
    parentOptions.value = withRootNode(result.data)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadTable()
}

function resetQuery() {
  Object.assign(query, {
    deptName: '',
    leader: '',
  })
  loadTable()
}

async function openCreate(parent?: DeptVO) {
  isEdit.value = false
  resetFormState()
  form.parentId = parent?.deptId ?? 0
  await loadTable()
  visible.value = true
}

async function openEdit(row: DeptVO) {
  isEdit.value = true
  resetFormState()
  const [deptRes, optionRes] = await Promise.all([getDept(row.deptId), listDeptExcludeChild(row.deptId)])
  Object.assign(form, deptRes.data)
  parentOptions.value = withRootNode(optionRes.data)
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  if (isEdit.value) {
    await updateDept(form)
    message.success('部门更新成功')
  } else {
    await createDept(form)
    message.success('部门创建成功')
  }
  visible.value = false
  await loadTable()
}

async function handleDelete(row: DeptVO) {
  await deleteDept(row.deptId)
  message.success('部门删除成功')
  await loadTable()
}

const columns: DataTableColumns<DeptVO> = [
  { title: '部门名称', key: 'deptName', width: 180 },
  { title: '负责人', key: 'leader', width: 120 },
  { title: '联系电话', key: 'phone', width: 140 },
  { title: '邮箱', key: 'email', width: 180 },
  { title: '排序', key: 'orderNum', width: 80 },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status }) },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    render: (row) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openCreate(row) }, { default: () => '新增下级' }),
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () =>
                h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => `确定删除部门“${row.deptName}”吗？`,
            },
          ),
        ],
      }),
  },
]

onMounted(loadTable)
</script>

<template>
  <ConsolePage title="部门管理" eyebrow="系统管理" description="维护组织架构、上下级关系、负责人和基础联系信息。">
    <template #actions>
      <NButton strong secondary type="primary" @click="openCreate()">新增部门</NButton>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.deptName" placeholder="部门名称" clearable class="max-w-[170px]" />
        <NInput v-model:value="query.leader" placeholder="负责人" clearable class="max-w-[170px]" />
        <NSpace>
          <NButton strong secondary type="primary" @click="handleSearch">搜索</NButton>
          <NButton strong secondary @click="resetQuery">重置</NButton>
        </NSpace>
      </div>

      <NDataTable
        :columns="columns"
        :data="rows"
        :loading="loading"
        :bordered="false"
        :row-key="(row: DeptVO) => row.deptId"
        children-key="children"
        default-expand-all
      />
    </NCard>

    <NModal v-model:show="visible">
      <div class="mx-auto w-[min(860px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑部门' : '新增部门' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="上级部门">
              <NTreeSelect v-model:value="form.parentId" :options="toNaiveTreeOptions(parentOptions)" default-expand-all />
            </NFormItem>
            <NFormItem label="部门名称" path="deptName">
              <NInput v-model:value="form.deptName" />
            </NFormItem>
            <NFormItem label="部门类别">
              <NInput v-model:value="form.deptCategory" />
            </NFormItem>
            <NFormItem label="显示排序">
              <NInputNumber v-model:value="form.orderNum" :min="0" class="w-full" />
            </NFormItem>
            <NFormItem label="负责人">
              <NInput v-model:value="form.leader" />
            </NFormItem>
            <NFormItem label="联系电话">
              <NInput v-model:value="form.phone" />
            </NFormItem>
            <NFormItem label="邮箱">
              <NInput v-model:value="form.email" />
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
