<template>
  <div class="p-2">
    <el-card shadow="hover" class="mb-[10px]">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="报价单号">
          <el-input v-model="queryParams.quotationId" placeholder="请输入报价单号" clearable />
        </el-form-item>
        <el-form-item label="询价单号">
          <el-input v-model="queryParams.inquiryId" placeholder="请输入询价单号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">查询</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="mb-[8px]">
        <el-tab-pane name="WAIT_PRICE_FILL" label="待补价" />
        <el-tab-pane name="MANUAL_WAIT_PRICE_FILL" label="待人工补价" />
        <el-tab-pane name="WAIT_SUBMIT" label="待提交" />
        <el-tab-pane name="COMPLETED" label="已完成" />
      </el-tabs>
      <el-table v-loading="loading" :data="quotationList" border>
        <el-table-column label="报价单号" prop="quotationId" min-width="150" />
        <el-table-column label="询价单号" prop="inquiryId" min-width="150" />
        <el-table-column label="状态" prop="flowStatus" min-width="120" />
        <el-table-column label="节点" prop="currentNodeName" min-width="120" />
        <el-table-column label="补价方式" width="110">
          <template #default="scope">
            <el-tag :type="scope.row.manualPriceFillEnabled ? 'warning' : 'success'">
              {{ scope.row.manualPriceFillEnabled ? '人工' : '自动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="明细数" prop="itemCount" width="80" />
        <el-table-column label="已补价" prop="quotedItemCount" width="90" />
        <el-table-column label="未补价" prop="unquoteItemCount" width="90" />
        <el-table-column label="异常" prop="exceptionItemCount" width="80" />
        <el-table-column label="最近更新时间" min-width="160">
          <template #default="scope">
            {{ proxy.parseTime(scope.row.lastLogTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openDetail(scope.row)">查看详情</el-button>
            <el-button link type="primary" @click="submitQuotation(scope.row)">手动提交</el-button>
            <el-button link type="danger" @click="retryQuotation(scope.row)">重试</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        :total="total"
        @pagination="getList"
      />
    </el-card>

    <el-drawer v-model="drawerVisible" title="报价单明细" size="60%">
      <el-table :data="itemList" border height="100%">
        <el-table-column label="配件编码" prop="partsNum" min-width="140" />
        <el-table-column label="配件名称" prop="partsName" min-width="160" />
        <el-table-column label="品牌" prop="brandName" min-width="120" />
        <el-table-column label="质量" prop="partsBrandQuality" min-width="100" />
        <el-table-column label="数量" prop="quantity" width="80" />
        <el-table-column label="建议价" prop="suggestedPrice" width="100" />
        <el-table-column label="最终价" prop="finalPrice" width="100" />
        <el-table-column label="状态" prop="itemProcessStatus" width="120" />
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup lang="ts" name="KaisiWorkbenchQuotation">
import { listKaisiQuotationItems, listKaisiQuotations, retryKaisiQuotation, submitKaisiQuotation } from '@/api/kaisi/workbench';
import { KaisiQuotationQuery, KaisiQuotationVO, KaisiQuoteItemVO } from '@/api/kaisi/workbench/types';

const { proxy } = getCurrentInstance() as ComponentInternalInstance;
const route = useRoute();

const loading = ref(false);
const total = ref(0);
const quotationList = ref<KaisiQuotationVO[]>([]);
const itemList = ref<KaisiQuoteItemVO[]>([]);
const drawerVisible = ref(false);
const activeRow = ref<KaisiQuotationVO>();
const activeTab = ref('WAIT_PRICE_FILL');

const queryParams = reactive<KaisiQuotationQuery>({
  pageNum: 1,
  pageSize: 10,
  quotationId: '',
  inquiryId: '',
  flowStatus: '',
  scene: 'TODAY'
});

// 查询报价单管理列表。
const getList = async () => {
  applyTabQuery();
  loading.value = true;
  const res = await listKaisiQuotations(queryParams);
  quotationList.value = res.rows || [];
  total.value = res.total || 0;
  loading.value = false;
};

const applyTabQuery = () => {
  queryParams.manualPriceFillEnabled = undefined;
  if (activeTab.value === 'MANUAL_WAIT_PRICE_FILL') {
    queryParams.flowStatus = 'WAIT_PRICE_FILL';
    queryParams.manualPriceFillEnabled = true;
  } else {
    queryParams.flowStatus = activeTab.value;
  }
};

const handleQuery = () => {
  queryParams.pageNum = 1;
  getList();
};

const resetQuery = () => {
  queryParams.quotationId = '';
  queryParams.inquiryId = '';
  handleQuery();
};

const handleTabChange = () => {
  queryParams.pageNum = 1;
  getList();
};

// 打开报价单明细抽屉。
const openDetail = async (row: KaisiQuotationVO) => {
  activeRow.value = row;
  const { data } = await listKaisiQuotationItems(row.quotationId, row.storeId);
  itemList.value = data || [];
  drawerVisible.value = true;
};

// 触发手动提交操作。
const submitQuotation = async (row: KaisiQuotationVO) => {
  await submitKaisiQuotation(row.quotationId, row.storeId);
  proxy?.$modal.msgSuccess('已触发手动提交');
  await getList();
};

// 触发重试操作。
const retryQuotation = async (row: KaisiQuotationVO) => {
  await retryKaisiQuotation(row.quotationId, row.storeId);
  proxy?.$modal.msgSuccess('已触发重试');
  await getList();
};

onMounted(() => {
  const tab = String(route.query.tab || '');
  if (tab === 'WAIT_SUBMIT' || tab === 'WAIT_PRICE_FILL' || tab === 'COMPLETED') {
    activeTab.value = tab;
  }
  getList();
});
</script>
