<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue'
import { NButton, NCard, NDataTable, NForm, NFormItem, NInput, NModal, NPopconfirm, NSelect, NSpace, NTreeSelect } from 'naive-ui'
import type { DataTableColumns, FormInst } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { changeUserStatus, createUser, deleteUser, getUser, listUsers, resetUserPassword, updateUser, userDeptTree } from '@/api/modules/system'
import type { TreeOptionNode, UserForm, UserVO } from '@/types/common'
import { formatDateTime } from '@/utils/format'
import { toNaiveTreeOptions } from '@/utils/tree'
import { message } from '@/utils/discrete'

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const visible = ref(false)
const isEdit = ref(false)
const rows = ref<UserVO[]>([])
const total = ref(0)
const roleOptions = ref<Array<{ label: string; value: string | number }>>([])
const postOptions = ref<Array<{ label: string; value: string | number }>>([])
const deptTree = ref<TreeOptionNode[]>([])
const deptOptions = ref(
  toNaiveTreeOptions([
    {
      id: 0,
      label: '全部部门',
      children: [],
    },
  ]),
)

const query = reactive({
  pageNum: 1,
  pageSize: 10,
  deptId: undefined as string | number | undefined,
  userName: '',
  phonenumber: '',
})

const form = reactive<UserForm>({
  userId: undefined,
  deptId: undefined,
  userName: '',
  nickName: '',
  password: 'Aa123456',
  phonenumber: '',
  email: '',
  sex: '0',
  status: '0',
  remark: '',
  postIds: [],
  roleIds: [],
})

function resetFormState() {
  Object.assign(form, {
    userId: undefined,
    deptId: undefined,
    userName: '',
    nickName: '',
    password: 'Aa123456',
    phonenumber: '',
    email: '',
    sex: '0',
    status: '0',
    remark: '',
    postIds: [],
    roleIds: [],
  })
}

async function loadDeptTree() {
  const result = await userDeptTree()
  deptTree.value = result.data
  deptOptions.value = toNaiveTreeOptions([
    {
      id: 0,
      label: '全部部门',
      children: result.data,
    },
  ])
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listUsers(query)
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
    userName: '',
    phonenumber: '',
    deptId: undefined,
    pageNum: 1,
  })
  loadTable()
}

async function loadEditOptions(userId?: string | number) {
  const result = await getUser(userId)
  roleOptions.value = result.data.roles.map((item) => ({ label: item.roleName, value: item.roleId }))
  postOptions.value = result.data.posts.map((item) => ({ label: item.postName, value: item.postId }))
  return result
}

async function openCreate() {
  isEdit.value = false
  resetFormState()
  await Promise.all([loadEditOptions(), loadDeptTree()])
  visible.value = true
}

async function openEdit(row: UserVO) {
  isEdit.value = true
  resetFormState()
  const [result] = await Promise.all([loadEditOptions(row.userId), loadDeptTree()])
  Object.assign(form, result.data.user, {
    roleIds: result.data.roleIds,
    postIds: result.data.postIds,
    password: '',
  })
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  if (isEdit.value) {
    await updateUser(form)
    message.success('用户更新成功')
  } else {
    await createUser(form)
    message.success('用户创建成功')
  }
  visible.value = false
  await loadTable()
}

async function handleDelete(row: UserVO) {
  await deleteUser(row.userId)
  message.success('用户删除成功')
  await loadTable()
}

async function handleStatus(row: UserVO) {
  const nextStatus = row.status === '0' ? '1' : '0'
  await changeUserStatus(row.userId, nextStatus)
  message.success('状态更新成功')
  await loadTable()
}

async function handleResetPassword(row: UserVO) {
  const password = window.prompt(`请输入用户 ${row.userName} 的新密码`, 'Aa123456')
  if (!password) {
    return
  }
  await resetUserPassword(row.userId, password)
  message.success('密码重置成功')
}

const columns: DataTableColumns<UserVO> = [
  { title: '用户名', key: 'userName', width: 140 },
  { title: '昵称', key: 'nickName', width: 140 },
  { title: '部门', key: 'deptName', width: 160 },
  { title: '手机号', key: 'phonenumber', width: 150 },
  { title: '邮箱', key: 'email', width: 220 },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status }) },
  {
    title: '最后登录',
    key: 'loginDate',
    width: 180,
    render: (row) => formatDateTime(row.loginDate),
  },
  {
    title: '操作',
    key: 'actions',
    width: 300,
    render: (row) =>
      h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', strong: true, secondary: true, onClick: () => handleStatus(row) }, { default: () => (row.status === '0' ? '停用' : '启用') }),
          h(
            NButton,
            { size: 'small', strong: true, secondary: true, type: 'warning', onClick: () => handleResetPassword(row) },
            { default: () => '重置密码' },
          ),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row) },
            {
              trigger: () =>
                h(NButton, { size: 'small', strong: true, secondary: true, type: 'error' }, { default: () => '删除' }),
              default: () => `确定删除用户“${row.userName}”吗？`,
            },
          ),
        ],
      }),
  },
]

onMounted(async () => {
  await Promise.all([loadTable(), loadDeptTree()])
})
</script>

<template>
  <ConsolePage title="用户管理" eyebrow="系统管理" description="维护用户资料、所属部门、角色岗位和账号状态。">
    <template #actions>
      <NButton strong secondary type="primary" @click="openCreate">新增用户</NButton>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.userName" placeholder="用户名" clearable class="max-w-[170px]" />
        <NInput v-model:value="query.phonenumber" placeholder="手机号" clearable class="max-w-[170px]" />
        <NTreeSelect
          v-model:value="query.deptId"
          clearable
          class="w-[170px]"
          placeholder="所属部门"
          :options="deptOptions"
          default-expand-all
        />
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
      <div class="mx-auto w-[min(920px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑用户' : '新增用户' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="所属部门" path="deptId">
              <NTreeSelect v-model:value="form.deptId" :options="deptOptions" default-expand-all />
            </NFormItem>
            <NFormItem label="用户名" path="userName">
              <NInput v-model:value="form.userName" :disabled="isEdit" />
            </NFormItem>
            <NFormItem label="昵称" path="nickName">
              <NInput v-model:value="form.nickName" />
            </NFormItem>
            <NFormItem v-if="!isEdit" label="密码" path="password">
              <NInput v-model:value="form.password" type="password" show-password-on="click" />
            </NFormItem>
            <NFormItem label="手机号">
              <NInput v-model:value="form.phonenumber" />
            </NFormItem>
            <NFormItem label="邮箱">
              <NInput v-model:value="form.email" />
            </NFormItem>
            <NFormItem label="性别">
              <NSelect
                v-model:value="form.sex"
                :options="[
                  { label: '男', value: '0' },
                  { label: '女', value: '1' },
                  { label: '未知', value: '2' },
                ]"
              />
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
            <NFormItem label="角色" class="md:col-span-2">
              <NSelect v-model:value="form.roleIds" multiple :options="roleOptions" />
            </NFormItem>
            <NFormItem label="岗位" class="md:col-span-2">
              <NSelect v-model:value="form.postIds" multiple :options="postOptions" />
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
