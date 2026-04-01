<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
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
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  NTree,
  NTreeSelect,
} from 'naive-ui'
import type { DataTableColumns, FormInst, TreeOption } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { createPost, deletePost, getPost, listPosts, postDeptTree, updatePost } from '@/api/modules/system'
import type { PostForm, PostVO, TreeOptionNode } from '@/types/common'
import { formatDateTime } from '@/utils/format'
import { toNaiveTreeOptions } from '@/utils/tree'
import { message } from '@/utils/discrete'

type TreeKey = string | number

const loading = ref(false)
const visible = ref(false)
const isEdit = ref(false)
const rows = ref<PostVO[]>([])
const total = ref(0)
const deptTreeNodes = ref<TreeOptionNode[]>([])
const selectedDeptKeys = ref<TreeKey[]>([])
const deptKeyword = ref('')
const formRef = ref<FormInst | null>(null)

const query = reactive({
  pageNum: 1,
  pageSize: 10,
  deptId: undefined as TreeKey | undefined,
  postCode: '',
  postName: '',
  postCategory: '',
  status: '',
})

const form = reactive<PostForm>({
  postId: undefined,
  deptId: undefined,
  postCode: '',
  postName: '',
  postCategory: '',
  postSort: 0,
  status: '0',
  remark: '',
})

function resetFormState() {
  Object.assign(form, {
    postId: undefined,
    deptId: undefined,
    postCode: '',
    postName: '',
    postCategory: '',
    postSort: 0,
    status: '0',
    remark: '',
  })
}

function filterTree(nodes: TreeOptionNode[], keyword: string): TreeOptionNode[] {
  if (!keyword.trim()) {
    return nodes
  }
  const normalized = keyword.trim().toLowerCase()
  const filtered: TreeOptionNode[] = []
  nodes.forEach((node) => {
    const children = filterTree(node.children ?? [], keyword)
    const matched = String(node.label).toLowerCase().includes(normalized)
    if (matched || children.length) {
      filtered.push({
        ...node,
        children,
      })
    }
  })
  return filtered
}

const filteredDeptTreeOptions = computed<TreeOption[]>(() => toNaiveTreeOptions(filterTree(deptTreeNodes.value, deptKeyword.value)))

const deptSelectOptions = computed(() =>
  toNaiveTreeOptions([
    {
      id: 0,
      label: '全部部门',
      children: deptTreeNodes.value,
    },
  ]),
)

async function loadDeptTree() {
  const result = await postDeptTree()
  deptTreeNodes.value = result.data
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listPosts(query)
    rows.value = result.rows
    total.value = result.total
  } finally {
    loading.value = false
  }
}

function handleDeptSelect(keys: TreeKey[]) {
  selectedDeptKeys.value = keys
  query.pageNum = 1
  query.deptId = keys[0]
  loadTable()
}

function resetFilters() {
  Object.assign(query, {
    pageNum: 1,
    deptId: undefined,
    postCode: '',
    postName: '',
    postCategory: '',
    status: '',
  })
  selectedDeptKeys.value = []
  loadTable()
}

function handleSearch() {
  query.pageNum = 1
  loadTable()
}

async function openCreate() {
  isEdit.value = false
  resetFormState()
  await loadDeptTree()
  visible.value = true
}

async function openEdit(row: PostVO) {
  isEdit.value = true
  resetFormState()
  const [postRes] = await Promise.all([getPost(row.postId), loadDeptTree()])
  Object.assign(form, postRes.data)
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  if (isEdit.value) {
    await updatePost(form)
    message.success('岗位更新成功')
  } else {
    await createPost(form)
    message.success('岗位创建成功')
  }
  visible.value = false
  await loadTable()
}

async function handleDelete(row: PostVO) {
  await deletePost(row.postId)
  message.success('岗位删除成功')
  await loadTable()
}

const columns: DataTableColumns<PostVO> = [
  { title: '岗位编码', key: 'postCode', width: 140 },
  { title: '分类编码', key: 'postCategory', width: 140 },
  { title: '岗位名称', key: 'postName', width: 180 },
  { title: '所属部门', key: 'deptName', width: 160 },
  { title: '排序', key: 'postSort', width: 80 },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status }) },
  {
    title: '创建时间',
    key: 'createTime',
    width: 180,
    render: (row) => formatDateTime(row.createTime),
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render: (row) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () =>
                h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => `确定删除岗位“${row.postName}”吗？`,
            },
          ),
        ],
      }),
  },
]

onMounted(async () => {
  await Promise.all([loadDeptTree(), loadTable()])
})
</script>

<template>
  <ConsolePage title="岗位管理" eyebrow="系统管理" description="维护岗位编码、岗位分类、所属部门和状态，支持按部门快速筛选岗位。">
    <template #actions>
      <NButton strong secondary type="primary" @click="openCreate">新增岗位</NButton>
    </template>

    <div class="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
      <NCard class="rounded-[20px] border-none">
        <div class="space-y-3">
          <div>
            <div class="mb-2 text-sm font-semibold text-[color:var(--text-main)]">部门筛选</div>
            <NInput v-model:value="deptKeyword" placeholder="搜索部门" clearable />
          </div>
          <div class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] p-3">
            <NTree
              block-line
              selectable
              default-expand-all
              key-field="key"
              label-field="label"
              children-field="children"
              :data="filteredDeptTreeOptions"
              :selected-keys="selectedDeptKeys"
              @update:selected-keys="(keys) => handleDeptSelect(keys as TreeKey[])"
            />
          </div>
        </div>
      </NCard>

      <NCard class="rounded-[20px] border-none">
        <div class="mb-4 flex flex-wrap items-center gap-2">
          <NInput v-model:value="query.postCode" placeholder="岗位编码" clearable class="max-w-[170px]" />
          <NInput v-model:value="query.postCategory" placeholder="分类编码" clearable class="max-w-[170px]" />
          <NInput v-model:value="query.postName" placeholder="岗位名称" clearable class="max-w-[170px]" />
          <NSelect
            v-model:value="query.status"
            clearable
            placeholder="状态"
            class="w-[150px]"
            :options="[
              { label: '启用', value: '0' },
              { label: '停用', value: '1' },
            ]"
          />
          <NSpace>
            <NButton strong secondary type="primary" @click="handleSearch">搜索</NButton>
            <NButton strong secondary @click="resetFilters">重置</NButton>
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
    </div>

    <NModal v-model:show="visible">
      <div class="mx-auto w-[min(860px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑岗位' : '新增岗位' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="所属部门" path="deptId">
              <NTreeSelect v-model:value="form.deptId" :options="deptSelectOptions" default-expand-all />
            </NFormItem>
            <NFormItem label="岗位名称" path="postName">
              <NInput v-model:value="form.postName" />
            </NFormItem>
            <NFormItem label="岗位编码" path="postCode">
              <NInput v-model:value="form.postCode" />
            </NFormItem>
            <NFormItem label="分类编码">
              <NInput v-model:value="form.postCategory" />
            </NFormItem>
            <NFormItem label="显示排序" path="postSort">
              <NInputNumber v-model:value="form.postSort" :min="0" class="w-full" />
            </NFormItem>
            <NFormItem label="岗位状态">
              <NRadioGroup v-model:value="form.status">
                <NSpace>
                  <NRadio value="0">启用</NRadio>
                  <NRadio value="1">停用</NRadio>
                </NSpace>
              </NRadioGroup>
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
