<template>
  <div class="p-2 kaisi-base-config">
    <el-card shadow="hover">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="font-600">开思平台基础配置</div>
          <div class="text-[12px] text-[#909399]">品牌 / 质量 / 质量品牌关联 / 平台扩展配置</div>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="品牌配置" name="brand">
          <el-form :inline="true" :model="brandQuery" class="mb-[8px]">
            <el-form-item label="品牌名称">
              <el-input v-model="brandQuery.brandName" placeholder="请输入品牌名称" clearable />
            </el-form-item>
            <el-form-item label="原始ID">
              <el-input v-model="brandQuery.brandOriginId" placeholder="请输入原始ID" clearable />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="brandQuery.status" placeholder="全部" clearable style="width: 120px">
                <el-option label="启用" :value="1" />
                <el-option label="停用" :value="0" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="queryBrandList">查询</el-button>
              <el-button icon="Refresh" @click="resetBrandQuery">重置</el-button>
              <el-button type="success" icon="Plus" @click="openBrandDialog()">新增品牌</el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="brandLoading" :data="brandList" border>
            <el-table-column label="ID" prop="id" width="90" />
            <el-table-column label="品牌名称" prop="brandName" min-width="160" />
            <el-table-column label="原始ID" prop="brandOriginId" min-width="180" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="160">
              <template #default="scope">
                {{ proxy?.parseTime(scope.row.updateTime) || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openBrandDialog(scope.row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteBrand(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <pagination
            v-show="brandTotal > 0"
            v-model:page="brandQuery.pageNum"
            v-model:limit="brandQuery.pageSize"
            :total="brandTotal"
            @pagination="getBrandList"
          />
        </el-tab-pane>

        <el-tab-pane label="质量配置" name="quality">
          <el-form :inline="true" :model="qualityQuery" class="mb-[8px]">
            <el-form-item label="质量编码">
              <el-input v-model="qualityQuery.qualityCode" placeholder="请输入质量编码" clearable />
            </el-form-item>
            <el-form-item label="质量名称">
              <el-input v-model="qualityQuery.qualityName" placeholder="请输入质量名称" clearable />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="qualityQuery.status" placeholder="全部" clearable style="width: 120px">
                <el-option label="启用" :value="1" />
                <el-option label="停用" :value="0" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="queryQualityList">查询</el-button>
              <el-button icon="Refresh" @click="resetQualityQuery">重置</el-button>
              <el-button type="success" icon="Plus" @click="openQualityDialog()">新增质量</el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="qualityLoading" :data="qualityList" border>
            <el-table-column label="ID" prop="id" width="90" />
            <el-table-column label="质量编码" prop="qualityCode" min-width="140" />
            <el-table-column label="质量名称" prop="qualityName" min-width="160" />
            <el-table-column label="原始ID" prop="qualityOriginId" min-width="180" />
            <el-table-column label="质量类型" prop="qualityType" width="100" />
            <el-table-column label="排序" prop="orderNum" width="90" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="160">
              <template #default="scope">
                {{ proxy?.parseTime(scope.row.updateTime) || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openQualityDialog(scope.row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteQuality(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <pagination
            v-show="qualityTotal > 0"
            v-model:page="qualityQuery.pageNum"
            v-model:limit="qualityQuery.pageSize"
            :total="qualityTotal"
            @pagination="getQualityList"
          />
        </el-tab-pane>

        <el-tab-pane label="质量品牌关联" name="link">
          <el-form :inline="true" :model="linkQuery" class="mb-[8px]">
            <el-form-item label="关键字">
              <el-input v-model="linkQuery.keyword" placeholder="质量/品牌名称" clearable />
            </el-form-item>
            <el-form-item label="质量">
              <el-select v-model="linkQuery.kaisiQualityId" placeholder="全部" clearable filterable style="width: 200px">
                <el-option v-for="item in qualityOptions" :key="item.id" :label="`${item.qualityCode} - ${item.qualityName}`" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="品牌">
              <el-select v-model="linkQuery.kaisiBrandId" placeholder="全部" clearable filterable style="width: 200px">
                <el-option v-for="item in brandOptions" :key="item.id" :label="item.brandName" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="queryLinkList">查询</el-button>
              <el-button icon="Refresh" @click="resetLinkQuery">重置</el-button>
              <el-button type="success" icon="Plus" @click="openLinkDialog()">新增关联</el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="linkLoading" :data="linkList" border>
            <el-table-column label="ID" prop="id" width="90" />
            <el-table-column label="质量编码" prop="qualityCode" min-width="120" />
            <el-table-column label="质量名称" prop="qualityName" min-width="150" />
            <el-table-column label="品牌名称" prop="brandName" min-width="150" />
            <el-table-column label="质量原始ID" prop="qualityOriginId" min-width="150" />
            <el-table-column label="品牌原始ID" prop="brandOriginId" min-width="150" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="160">
              <template #default="scope">
                {{ proxy?.parseTime(scope.row.updateTime) || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openLinkDialog(scope.row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteLink(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <pagination
            v-show="linkTotal > 0"
            v-model:page="linkQuery.pageNum"
            v-model:limit="linkQuery.pageSize"
            :total="linkTotal"
            @pagination="getLinkList"
          />
        </el-tab-pane>

        <el-tab-pane label="平台扩展配置" name="platform-advanced">
          <PlatformAdvanced />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="brandDialogVisible" :title="brandForm.id ? '编辑品牌' : '新增品牌'" width="520px">
      <el-form ref="brandFormRef" :model="brandForm" :rules="brandRules" label-width="96px">
        <el-form-item label="品牌名称" prop="brandName">
          <el-input v-model="brandForm.brandName" placeholder="请输入品牌名称" />
        </el-form-item>
        <el-form-item label="原始ID" prop="brandOriginId">
          <el-input v-model="brandForm.brandOriginId" placeholder="请输入开思原始品牌ID" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="brandForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brandDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitBrand">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="qualityDialogVisible" :title="qualityForm.id ? '编辑质量' : '新增质量'" width="560px">
      <el-form ref="qualityFormRef" :model="qualityForm" :rules="qualityRules" label-width="96px">
        <el-form-item label="质量编码" prop="qualityCode">
          <el-input v-model="qualityForm.qualityCode" placeholder="请输入质量编码" />
        </el-form-item>
        <el-form-item label="质量名称" prop="qualityName">
          <el-input v-model="qualityForm.qualityName" placeholder="请输入质量名称" />
        </el-form-item>
        <el-form-item label="原始ID" prop="qualityOriginId">
          <el-input v-model="qualityForm.qualityOriginId" placeholder="请输入开思原始质量ID" />
        </el-form-item>
        <el-form-item label="质量类型">
          <el-input-number v-model="qualityForm.qualityType" :min="0" :max="99" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="qualityForm.orderNum" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="qualityForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="qualityDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitQuality">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="linkDialogVisible" :title="linkForm.id ? '编辑关联' : '新增关联'" width="560px">
      <el-form ref="linkFormRef" :model="linkForm" :rules="linkRules" label-width="96px">
        <el-form-item label="质量" prop="kaisiQualityId">
          <el-select v-model="linkForm.kaisiQualityId" filterable style="width: 100%" placeholder="请选择质量">
            <el-option v-for="item in qualityOptions" :key="item.id" :label="`${item.qualityCode} - ${item.qualityName}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌" prop="kaisiBrandId">
          <el-select v-model="linkForm.kaisiBrandId" filterable style="width: 100%" placeholder="请选择品牌">
            <el-option v-for="item in brandOptions" :key="item.id" :label="item.brandName" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="linkForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="linkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitLink">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="KaisiWorkbenchBaseConfig">
import {
  addKaisiBrand,
  addKaisiQuality,
  addKaisiQualityBrandLink,
  deleteKaisiBrand,
  deleteKaisiQuality,
  deleteKaisiQualityBrandLink,
  listKaisiBrandOptions,
  listKaisiBrands,
  listKaisiQualities,
  listKaisiQualityBrandLinks,
  listKaisiQualityOptions,
  updateKaisiBrand,
  updateKaisiQuality,
  updateKaisiQualityBrandLink
} from '@/api/kaisi/base-config';
import {
  KaisiBrandForm,
  KaisiBrandQuery,
  KaisiBrandVO,
  KaisiQualityBrandLinkForm,
  KaisiQualityBrandLinkQuery,
  KaisiQualityBrandLinkVO,
  KaisiQualityForm,
  KaisiQualityQuery,
  KaisiQualityVO
} from '@/api/kaisi/base-config/types';
import { FormInstance, FormRules } from 'element-plus';
import PlatformAdvanced from './components/platform-advanced.vue';

const { proxy } = getCurrentInstance() as ComponentInternalInstance;
const activeTab = ref('brand');
const submitLoading = ref(false);

const brandLoading = ref(false);
const brandTotal = ref(0);
const brandList = ref<KaisiBrandVO[]>([]);
const brandOptions = ref<KaisiBrandVO[]>([]);
const brandQuery = reactive<KaisiBrandQuery>({
  pageNum: 1,
  pageSize: 10
});
const brandDialogVisible = ref(false);
const brandFormRef = ref<FormInstance>();
const brandForm = reactive<KaisiBrandForm>({
  brandName: '',
  brandOriginId: '',
  status: 1
});
const brandRules = reactive<FormRules>({
  brandName: [{ required: true, message: '请输入品牌名称', trigger: 'blur' }],
  brandOriginId: [{ required: true, message: '请输入原始ID', trigger: 'blur' }]
});

const qualityLoading = ref(false);
const qualityTotal = ref(0);
const qualityList = ref<KaisiQualityVO[]>([]);
const qualityOptions = ref<KaisiQualityVO[]>([]);
const qualityQuery = reactive<KaisiQualityQuery>({
  pageNum: 1,
  pageSize: 10
});
const qualityDialogVisible = ref(false);
const qualityFormRef = ref<FormInstance>();
const qualityForm = reactive<KaisiQualityForm>({
  qualityCode: '',
  qualityName: '',
  qualityOriginId: '',
  qualityType: 0,
  orderNum: 0,
  status: 1
});
const qualityRules = reactive<FormRules>({
  qualityCode: [{ required: true, message: '请输入质量编码', trigger: 'blur' }],
  qualityName: [{ required: true, message: '请输入质量名称', trigger: 'blur' }],
  qualityOriginId: [{ required: true, message: '请输入原始ID', trigger: 'blur' }]
});

const linkLoading = ref(false);
const linkTotal = ref(0);
const linkList = ref<KaisiQualityBrandLinkVO[]>([]);
const linkQuery = reactive<KaisiQualityBrandLinkQuery>({
  pageNum: 1,
  pageSize: 10
});
const linkDialogVisible = ref(false);
const linkFormRef = ref<FormInstance>();
const linkForm = reactive<KaisiQualityBrandLinkForm>({
  kaisiQualityId: undefined,
  kaisiBrandId: undefined,
  status: 1
});
const linkRules = reactive<FormRules>({
  kaisiQualityId: [{ required: true, message: '请选择质量', trigger: 'change' }],
  kaisiBrandId: [{ required: true, message: '请选择品牌', trigger: 'change' }]
});

// 按页签加载当前主数据。
const handleTabChange = async () => {
  if (activeTab.value === 'brand') {
    await getBrandList();
    return;
  }
  if (activeTab.value === 'quality') {
    await getQualityList();
    return;
  }
  if (activeTab.value === 'platform-advanced') {
    return;
  }
  await getLinkList();
};

const getBrandList = async () => {
  brandLoading.value = true;
  const res = await listKaisiBrands(brandQuery);
  brandList.value = res.rows || [];
  brandTotal.value = res.total || 0;
  brandLoading.value = false;
};

const queryBrandList = () => {
  brandQuery.pageNum = 1;
  getBrandList();
};

const resetBrandQuery = () => {
  brandQuery.brandName = '';
  brandQuery.brandOriginId = '';
  brandQuery.status = undefined;
  queryBrandList();
};

const openBrandDialog = (row?: KaisiBrandVO) => {
  if (row) {
    brandForm.id = row.id;
    brandForm.brandName = row.brandName;
    brandForm.brandOriginId = row.brandOriginId;
    brandForm.status = row.status;
  } else {
    brandForm.id = undefined;
    brandForm.brandName = '';
    brandForm.brandOriginId = '';
    brandForm.status = 1;
  }
  brandDialogVisible.value = true;
};

const submitBrand = async () => {
  await brandFormRef.value?.validate();
  submitLoading.value = true;
  if (brandForm.id) {
    await updateKaisiBrand(brandForm);
    proxy?.$modal.msgSuccess('品牌修改成功');
  } else {
    await addKaisiBrand(brandForm);
    proxy?.$modal.msgSuccess('品牌新增成功');
  }
  submitLoading.value = false;
  brandDialogVisible.value = false;
  await loadOptions();
  await getBrandList();
};

const handleDeleteBrand = async (row: KaisiBrandVO) => {
  await proxy?.$modal.confirm(`确认删除品牌【${row.brandName}】吗？`);
  await deleteKaisiBrand(row.id);
  proxy?.$modal.msgSuccess('删除成功');
  await loadOptions();
  await getBrandList();
};

const getQualityList = async () => {
  qualityLoading.value = true;
  const res = await listKaisiQualities(qualityQuery);
  qualityList.value = res.rows || [];
  qualityTotal.value = res.total || 0;
  qualityLoading.value = false;
};

const queryQualityList = () => {
  qualityQuery.pageNum = 1;
  getQualityList();
};

const resetQualityQuery = () => {
  qualityQuery.qualityCode = '';
  qualityQuery.qualityName = '';
  qualityQuery.qualityOriginId = '';
  qualityQuery.status = undefined;
  queryQualityList();
};

const openQualityDialog = (row?: KaisiQualityVO) => {
  if (row) {
    qualityForm.id = row.id;
    qualityForm.qualityCode = row.qualityCode;
    qualityForm.qualityName = row.qualityName;
    qualityForm.qualityOriginId = row.qualityOriginId;
    qualityForm.qualityType = row.qualityType || 0;
    qualityForm.orderNum = row.orderNum || 0;
    qualityForm.status = row.status;
  } else {
    qualityForm.id = undefined;
    qualityForm.qualityCode = '';
    qualityForm.qualityName = '';
    qualityForm.qualityOriginId = '';
    qualityForm.qualityType = 0;
    qualityForm.orderNum = 0;
    qualityForm.status = 1;
  }
  qualityDialogVisible.value = true;
};

const submitQuality = async () => {
  await qualityFormRef.value?.validate();
  submitLoading.value = true;
  if (qualityForm.id) {
    await updateKaisiQuality(qualityForm);
    proxy?.$modal.msgSuccess('质量修改成功');
  } else {
    await addKaisiQuality(qualityForm);
    proxy?.$modal.msgSuccess('质量新增成功');
  }
  submitLoading.value = false;
  qualityDialogVisible.value = false;
  await loadOptions();
  await getQualityList();
};

const handleDeleteQuality = async (row: KaisiQualityVO) => {
  await proxy?.$modal.confirm(`确认删除质量【${row.qualityName}】吗？`);
  await deleteKaisiQuality(row.id);
  proxy?.$modal.msgSuccess('删除成功');
  await loadOptions();
  await getQualityList();
};

const getLinkList = async () => {
  linkLoading.value = true;
  const res = await listKaisiQualityBrandLinks(linkQuery);
  linkList.value = res.rows || [];
  linkTotal.value = res.total || 0;
  linkLoading.value = false;
};

const queryLinkList = () => {
  linkQuery.pageNum = 1;
  getLinkList();
};

const resetLinkQuery = () => {
  linkQuery.keyword = '';
  linkQuery.kaisiQualityId = undefined;
  linkQuery.kaisiBrandId = undefined;
  linkQuery.status = undefined;
  queryLinkList();
};

const openLinkDialog = (row?: KaisiQualityBrandLinkVO) => {
  if (row) {
    linkForm.id = row.id;
    linkForm.kaisiQualityId = row.kaisiQualityId;
    linkForm.kaisiBrandId = row.kaisiBrandId;
    linkForm.status = row.status;
  } else {
    linkForm.id = undefined;
    linkForm.kaisiQualityId = undefined;
    linkForm.kaisiBrandId = undefined;
    linkForm.status = 1;
  }
  linkDialogVisible.value = true;
};

const submitLink = async () => {
  await linkFormRef.value?.validate();
  submitLoading.value = true;
  if (linkForm.id) {
    await updateKaisiQualityBrandLink(linkForm);
    proxy?.$modal.msgSuccess('关联修改成功');
  } else {
    await addKaisiQualityBrandLink(linkForm);
    proxy?.$modal.msgSuccess('关联新增成功');
  }
  submitLoading.value = false;
  linkDialogVisible.value = false;
  await getLinkList();
};

const handleDeleteLink = async (row: KaisiQualityBrandLinkVO) => {
  await proxy?.$modal.confirm(`确认删除关联【${row.qualityName} / ${row.brandName}】吗？`);
  await deleteKaisiQualityBrandLink(row.id);
  proxy?.$modal.msgSuccess('删除成功');
  await getLinkList();
};

const loadOptions = async () => {
  const [brandRes, qualityRes] = await Promise.all([listKaisiBrandOptions(), listKaisiQualityOptions()]);
  brandOptions.value = brandRes.data || [];
  qualityOptions.value = qualityRes.data || [];
};

onMounted(async () => {
  await loadOptions();
  await getBrandList();
});
</script>

<style scoped lang="scss">
.kaisi-base-config {
  :deep(.el-tabs__header) {
    margin-bottom: 12px;
  }
}
</style>
