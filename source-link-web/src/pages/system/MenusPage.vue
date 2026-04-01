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
  NTag,
  NTree,
  NTreeSelect,
} from 'naive-ui'
import type { DataTableColumns, FormInst } from 'naive-ui'
import ConsolePage from '@/components/ConsolePage.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { cascadeDeleteMenu, createMenu, deleteMenu, getMenu, listMenus, menuTreeSelect, updateMenu } from '@/api/modules/system'
import type { MenuForm, MenuVO, TreeOptionNode } from '@/types/common'
import { toNaiveTreeOptions } from '@/utils/tree'
import { message } from '@/utils/discrete'

type TreeKey = string | number

const loading = ref(false)
const visible = ref(false)
const cascadeVisible = ref(false)
const isEdit = ref(false)
const rows = ref<MenuVO[]>([])
const menuTreeNodes = ref<TreeOptionNode[]>([])
const cascadeKeys = ref<TreeKey[]>([])
const formRef = ref<FormInst | null>(null)

const query = reactive({
  menuName: '',
  status: '',
})

const form = reactive<MenuForm>({
  menuId: undefined,
  parentId: 0,
  menuName: '',
  orderNum: 0,
  path: '',
  component: '',
  queryParam: '',
  isFrame: '1',
  isCache: '0',
  menuType: 'M',
  visible: '0',
  status: '0',
  icon: '',
  remark: '',
  perms: '',
})

const parentTreeOptions = computed(() =>
  toNaiveTreeOptions([
    {
      id: 0,
      label: '主类目',
      children: menuTreeNodes.value,
    },
  ]),
)

const cascadeTreeOptions = computed(() => toNaiveTreeOptions(menuTreeNodes.value))

const menuTypeOptions = [
  { label: '目录', value: 'M' },
  { label: '菜单', value: 'C' },
  { label: '按钮', value: 'F' },
]

function resetFormState() {
  Object.assign(form, {
    menuId: undefined,
    parentId: 0,
    menuName: '',
    orderNum: 0,
    path: '',
    component: '',
    queryParam: '',
    isFrame: '1',
    isCache: '0',
    menuType: 'M',
    visible: '0',
    status: '0',
    icon: '',
    remark: '',
    perms: '',
  })
}

async function loadTable() {
  loading.value = true
  try {
    const result = await listMenus(query)
    rows.value = result.data
  } finally {
    loading.value = false
  }
}

async function loadTreeOptions() {
  const result = await menuTreeSelect()
  menuTreeNodes.value = result.data
}

function handleSearch() {
  loadTable()
}

function resetQuery() {
  Object.assign(query, {
    menuName: '',
    status: '',
  })
  loadTable()
}

async function openCreate(parent?: MenuVO) {
  isEdit.value = false
  resetFormState()
  await loadTreeOptions()
  form.parentId = parent?.menuId ?? 0
  visible.value = true
}

async function openEdit(row: MenuVO) {
  isEdit.value = true
  resetFormState()
  const [menuRes] = await Promise.all([getMenu(row.menuId), loadTreeOptions()])
  Object.assign(form, menuRes.data)
  visible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  if (isEdit.value) {
    await updateMenu(form)
    message.success('菜单更新成功')
  } else {
    await createMenu(form)
    message.success('菜单创建成功')
  }
  visible.value = false
  await Promise.all([loadTable(), loadTreeOptions()])
}

async function handleDelete(row: MenuVO) {
  await deleteMenu(row.menuId)
  message.success('菜单删除成功')
  await Promise.all([loadTable(), loadTreeOptions()])
}

async function openCascadeDelete() {
  await loadTreeOptions()
  cascadeKeys.value = []
  cascadeVisible.value = true
}

async function submitCascadeDelete() {
  if (!cascadeKeys.value.length) {
    message.warning('请先勾选要删除的菜单')
    return
  }
  await cascadeDeleteMenu(cascadeKeys.value)
  cascadeVisible.value = false
  message.success('级联删除成功')
  await Promise.all([loadTable(), loadTreeOptions()])
}

function updateCascadeKeys(keys: TreeKey[]) {
  cascadeKeys.value = keys
}

function renderMenuType(type?: string) {
  if (type === 'M') {
    return h(NTag, { round: true, type: 'info', size: 'small' }, { default: () => '目录' })
  }
  if (type === 'C') {
    return h(NTag, { round: true, type: 'success', size: 'small' }, { default: () => '菜单' })
  }
  return h(NTag, { round: true, type: 'warning', size: 'small' }, { default: () => '按钮' })
}

function renderYesNo(value?: string, yesText = '是', noText = '否') {
  return value === '0' ? yesText : noText
}

const columns: DataTableColumns<MenuVO> = [
  { title: '菜单名称', key: 'menuName', width: 180 },
  { title: '类型', key: 'menuType', width: 90, render: (row) => renderMenuType(row.menuType) },
  { title: '排序', key: 'orderNum', width: 80 },
  { title: '路由地址', key: 'path', ellipsis: { tooltip: true } },
  { title: '组件路径', key: 'component', ellipsis: { tooltip: true } },
  { title: '权限标识', key: 'perms', ellipsis: { tooltip: true } },
  { title: '显示', key: 'visible', width: 90, render: (row) => renderYesNo(row.visible, '显示', '隐藏') },
  { title: '缓存', key: 'isCache', width: 90, render: (row) => renderYesNo(row.isCache, '缓存', '不缓存') },
  { title: '状态', key: 'status', width: 90, render: (row) => h(StatusBadge, { value: row.status || '0' }) },
  {
    title: '操作',
    key: 'actions',
    width: 240,
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
              default: () => `确定删除菜单“${row.menuName}”吗？`,
            },
          ),
        ],
      }),
  },
]

onMounted(async () => {
  await Promise.all([loadTable(), loadTreeOptions()])
})
</script>

<template>
  <ConsolePage title="菜单管理" eyebrow="系统管理" description="维护目录、菜单、按钮权限与前端路由信息，支持新增下级和级联删除。">
    <template #actions>
      <NButton strong secondary type="error" @click="openCascadeDelete">级联删除</NButton>
      <NButton strong secondary type="primary" @click="openCreate()">新增菜单</NButton>
    </template>

    <NCard class="rounded-[20px] border-none">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <NInput v-model:value="query.menuName" placeholder="菜单名称" clearable class="max-w-[170px]" />
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
          <NButton strong secondary @click="resetQuery">重置</NButton>
        </NSpace>
      </div>

      <NDataTable
        :columns="columns"
        :data="rows"
        :loading="loading"
        :bordered="false"
        :row-key="(row: MenuVO) => row.menuId"
        children-key="children"
        default-expand-all
      />
    </NCard>

    <NModal v-model:show="visible">
      <div class="mx-auto w-[min(980px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">{{ isEdit ? '编辑菜单' : '新增菜单' }}</h3>
        <NForm ref="formRef" :model="form" label-placement="top">
          <div class="grid gap-4 md:grid-cols-2">
            <NFormItem label="上级菜单" class="md:col-span-2">
              <NTreeSelect v-model:value="form.parentId" :options="parentTreeOptions" default-expand-all />
            </NFormItem>
            <NFormItem label="菜单类型" class="md:col-span-2">
              <NRadioGroup v-model:value="form.menuType">
                <NSpace>
                  <NRadio v-for="item in menuTypeOptions" :key="item.value" :value="item.value">{{ item.label }}</NRadio>
                </NSpace>
              </NRadioGroup>
            </NFormItem>
            <NFormItem label="菜单名称" path="menuName">
              <NInput v-model:value="form.menuName" />
            </NFormItem>
            <NFormItem label="显示排序" path="orderNum">
              <NInputNumber v-model:value="form.orderNum" :min="0" class="w-full" />
            </NFormItem>
            <NFormItem v-if="form.menuType !== 'F'" label="路由地址" path="path">
              <NInput v-model:value="form.path" placeholder="例如 /system/user" />
            </NFormItem>
            <NFormItem v-if="form.menuType === 'C'" label="组件路径" path="component">
              <NInput v-model:value="form.component" placeholder="例如 system/user/index" />
            </NFormItem>
            <NFormItem v-if="form.menuType !== 'M'" label="权限标识" path="perms">
              <NInput v-model:value="form.perms" placeholder="例如 system:user:list" />
            </NFormItem>
            <NFormItem v-if="form.menuType === 'C'" label="路由参数">
              <NInput v-model:value="form.queryParam" placeholder='例如 {"id":1}' />
            </NFormItem>
            <NFormItem v-if="form.menuType !== 'F'" label="图标">
              <NInput v-model:value="form.icon" placeholder="请输入图标名称" />
            </NFormItem>
            <NFormItem v-if="form.menuType !== 'F'" label="是否外链">
              <NRadioGroup v-model:value="form.isFrame">
                <NSpace>
                  <NRadio value="0">是</NRadio>
                  <NRadio value="1">否</NRadio>
                </NSpace>
              </NRadioGroup>
            </NFormItem>
            <NFormItem v-if="form.menuType === 'C'" label="是否缓存">
              <NRadioGroup v-model:value="form.isCache">
                <NSpace>
                  <NRadio value="0">缓存</NRadio>
                  <NRadio value="1">不缓存</NRadio>
                </NSpace>
              </NRadioGroup>
            </NFormItem>
            <NFormItem v-if="form.menuType !== 'F'" label="显示状态">
              <NRadioGroup v-model:value="form.visible">
                <NSpace>
                  <NRadio value="0">显示</NRadio>
                  <NRadio value="1">隐藏</NRadio>
                </NSpace>
              </NRadioGroup>
            </NFormItem>
            <NFormItem label="菜单状态">
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

    <NModal v-model:show="cascadeVisible">
      <div class="mx-auto w-[min(840px,94vw)] rounded-[20px] bg-[color:var(--panel)] p-5 shadow-[0_24px_80px_rgba(16,24,40,0.18)]">
        <h3 class="mb-4 text-lg font-semibold">级联删除菜单</h3>
        <div class="rounded-2xl border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] p-4">
          <p class="mb-3 text-sm text-[color:var(--text-secondary)]">勾选后会连同子菜单一起删除，请谨慎操作。</p>
          <NTree
            checkable
            cascade
            block-line
            default-expand-all
            :data="cascadeTreeOptions"
            :checked-keys="cascadeKeys"
            @update:checked-keys="(keys) => updateCascadeKeys(keys as TreeKey[])"
          />
        </div>
        <div class="mt-4 flex justify-end gap-3">
          <NButton strong secondary @click="cascadeVisible = false">取消</NButton>
          <NButton strong secondary type="error" @click="submitCascadeDelete">确认删除</NButton>
        </div>
      </div>
    </NModal>
  </ConsolePage>
</template>
