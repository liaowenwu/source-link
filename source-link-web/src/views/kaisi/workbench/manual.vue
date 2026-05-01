<template>
  <div class="p-2">
    <el-row :gutter="12">
      <el-col :xs="24" :md="10">
        <el-card shadow="hover">
          <template #header>待人工补价报价单</template>
          <el-table v-loading="loading" :data="quotationList" height="620" @row-click="handleSelectQuotation">
            <el-table-column label="报价单号" prop="quotationId" min-width="150" />
            <el-table-column label="未补价" prop="unquoteItemCount" width="90" />
            <el-table-column label="异常" width="80">
              <template #default="scope">
                <el-tag v-if="scope.row.needAlert" type="danger">是</el-tag>
                <span v-else>否</span>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="160">
              <template #default="scope">
                {{ proxy.parseTime(scope.row.lastLogTime) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="14">
        <el-card shadow="hover">
          <template #header>
            {{ activeQuotation ? `报价单明细补价：${activeQuotation.quotationId}` : '报价单明细补价' }}
          </template>
          <el-table :data="itemList" border height="620">
            <el-table-column label="配件编码" prop="partsNum" min-width="130" />
            <el-table-column label="配件名称" prop="partsName" min-width="160" />
            <el-table-column label="品牌" prop="brandName" min-width="120" />
            <el-table-column label="建议价" prop="suggestedPrice" width="100" />
            <el-table-column label="最终报价" width="140">
              <template #default="scope">
                <el-input-number v-model="scope.row.finalPrice" :precision="2" :min="0" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column label="未匹配原因" min-width="180">
              <template #default="scope">
                <el-input v-model="scope.row.unmatchedReason" clearable placeholder="可选" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button type="primary" link @click="saveItem(scope.row)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="mt-[10px]">
            <el-button type="primary" :disabled="!activeQuotation" @click="submitQuotation">提交到待提交</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="KaisiWorkbenchManualPrice">
import {
  listKaisiQuotationItems,
  listKaisiQuotations,
  saveKaisiManualPrice,
  submitKaisiQuotation
} from '@/api/kaisi/workbench';
import { KaisiManualPriceForm, KaisiQuotationVO, KaisiQuoteItemVO } from '@/api/kaisi/workbench/types';

const { proxy } = getCurrentInstance() as ComponentInternalInstance;

const loading = ref(false);
const quotationList = ref<KaisiQuotationVO[]>([]);
const itemList = ref<KaisiQuoteItemVO[]>([]);
const activeQuotation = ref<KaisiQuotationVO>();

// 查询“待人工补价”列表。
const loadQuotationList = async () => {
  loading.value = true;
  const res = await listKaisiQuotations({
    pageNum: 1,
    pageSize: 200,
    flowStatus: 'WAIT_PRICE_FILL',
    scene: 'MANUAL'
  });
  quotationList.value = res.rows || [];
  loading.value = false;
};

// 切换报价单时加载右侧明细。
const handleSelectQuotation = async (row: KaisiQuotationVO) => {
  activeQuotation.value = row;
  const { data } = await listKaisiQuotationItems(row.quotationId, row.storeId);
  itemList.value = data || [];
};

// 保存单条人工补价。
const saveItem = async (row: KaisiQuoteItemVO) => {
  const form: KaisiManualPriceForm = {
    itemId: row.id,
    quotationId: row.quotationId,
    storeId: row.storeId,
    finalPrice: Number(row.finalPrice || 0),
    unmatchedReason: row.unmatchedReason,
    remark: row.remark
  };
  await saveKaisiManualPrice(form);
  proxy?.$modal.msgSuccess('保存成功');
};

// 提交当前报价单到待提交。
const submitQuotation = async () => {
  if (!activeQuotation.value) return;
  await submitKaisiQuotation(activeQuotation.value.quotationId, activeQuotation.value.storeId);
  proxy?.$modal.msgSuccess('已提交到待提交');
  await loadQuotationList();
};

onMounted(async () => {
  await loadQuotationList();
  if (quotationList.value.length > 0) {
    await handleSelectQuotation(quotationList.value[0]);
  }
});
</script>

