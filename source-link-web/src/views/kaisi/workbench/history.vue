<template>
  <div class="p-2">
    <el-card shadow="hover" class="mb-[10px]">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="时间区间">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="报价单号">
          <el-input v-model="queryParams.quotationId" clearable placeholder="请输入报价单号" />
        </el-form-item>
        <el-form-item label="零件关键词">
          <el-input v-model="partsKeyword" clearable placeholder="零件编码/名称" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">查询</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover">
      <el-table v-loading="loading" :data="historyParts" border>
        <el-table-column label="零件编码" prop="partsNum" min-width="140" />
        <el-table-column label="零件名称" prop="partsName" min-width="160" />
        <el-table-column label="品牌" prop="brandName" min-width="120" />
        <el-table-column label="质量" prop="partsBrandQuality" min-width="100" />
        <el-table-column label="报价次数" prop="quoteTimes" width="100" />
        <el-table-column label="平均报价" width="120">
          <template #default="scope">
            {{ scope.row.avgFinalPrice ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="最近报价时间" min-width="160">
          <template #default="scope">
            {{ proxy.parseTime(scope.row.latestQuoteTime) }}
          </template>
        </el-table-column>
        <el-table-column label="详情" width="120" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openTrend(scope.row)">查看走势</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="trendDialogVisible" :title="trendTitle" width="72%">
      <el-table :data="trendPoints" border max-height="520">
        <el-table-column label="报价时间" min-width="160">
          <template #default="scope">
            {{ proxy.parseTime(scope.row.quoteTime) }}
          </template>
        </el-table-column>
        <el-table-column label="报价单号" prop="quotationId" min-width="160" />
        <el-table-column label="门店" prop="storeId" min-width="100" />
        <el-table-column label="品牌" prop="brandName" min-width="120" />
        <el-table-column label="质量" prop="partsBrandQuality" min-width="100" />
        <el-table-column label="建议价" prop="suggestedPrice" width="100" />
        <el-table-column label="最终价" prop="finalPrice" width="100" />
      </el-table>
      <el-empty v-if="trendPoints.length === 0" description="该时间区间暂无价格走势数据" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="KaisiWorkbenchHistory">
import { listKaisiHistoryParts, listKaisiPriceTrend } from '@/api/kaisi/workbench';
import { KaisiHistoryPartVO, KaisiPriceTrendPointVO, KaisiQuotationQuery } from '@/api/kaisi/workbench/types';

const { proxy } = getCurrentInstance() as ComponentInternalInstance;

const loading = ref(false);
const partsKeyword = ref('');
const dateRange = ref<string[]>([]);
const historyParts = ref<KaisiHistoryPartVO[]>([]);
const trendPoints = ref<KaisiPriceTrendPointVO[]>([]);
const trendDialogVisible = ref(false);
const trendTitle = ref('价格走势');

const queryParams = reactive<KaisiQuotationQuery>({
  pageNum: 1,
  pageSize: 500,
  quotationId: '',
  scene: 'HISTORY',
  beginTime: '',
  endTime: ''
});

// 查询历史零件列表。
const getList = async () => {
  queryParams.beginTime = dateRange.value?.[0] || '';
  queryParams.endTime = dateRange.value?.[1] || '';
  loading.value = true;
  const { data } = await listKaisiHistoryParts({
    beginTime: queryParams.beginTime,
    endTime: queryParams.endTime,
    quotationId: queryParams.quotationId,
    partsKeyword: partsKeyword.value
  });
  historyParts.value = data || [];
  loading.value = false;
};

const handleQuery = () => {
  queryParams.pageNum = 1;
  getList();
};

const resetQuery = () => {
  dateRange.value = [];
  queryParams.quotationId = '';
  partsKeyword.value = '';
  handleQuery();
};

// 查看某零件价格走势（按品牌、质量区分）。
const openTrend = async (row: KaisiHistoryPartVO) => {
  trendTitle.value = `价格走势 - ${row.partsNum} / ${row.brandName || '-'} / ${row.partsBrandQuality || '-'}`;
  const { data } = await listKaisiPriceTrend({
    beginTime: queryParams.beginTime,
    endTime: queryParams.endTime,
    quotationId: queryParams.quotationId,
    partsNum: row.partsNum,
    brandName: row.brandName,
    partsBrandQuality: row.partsBrandQuality
  });
  trendPoints.value = data || [];
  trendDialogVisible.value = true;
};

onMounted(() => {
  getList();
});
</script>
