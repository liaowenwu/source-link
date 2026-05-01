<template>
  <div class="p-2 kaisi-workbench-settings">
    <el-card shadow="hover" class="setting-hero">
      <div class="hero-copy">
        <div class="hero-kicker">开思工作台</div>
        <div class="hero-title">基础配置</div>
        <div class="hero-desc">按平台配置抓取质量、品牌、区域和供应商规则；全局控制抓取策略、自动补价、自动提交和并发参数。</div>
      </div>
      <div class="hero-actions">
        <el-button icon="Refresh" @click="loadSetting">重新加载</el-button>
        <el-button type="primary" icon="Check" :loading="saveLoading" @click="handleSave">保存配置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="mt-[10px]">
      <template #header>
        <div class="section-title">
          <span>全局开关与策略</span>
          <small>写入 t_user_kaisi_config</small>
        </div>
      </template>
      <el-form :model="settingForm" label-width="150px">
        <el-row :gutter="16">
          <el-col :xs="24" :lg="12">
            <el-form-item label="启用平台">
              <el-checkbox-group v-model="settingForm.selectedPlatformCodes">
                <el-checkbox v-for="item in platformOptions" :key="item.platformCode" :label="item.platformCode">
                  {{ item.platformName }}
                </el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-form-item label="抓取策略">
              <el-radio-group v-model="settingForm.crawlStrategyType">
                <el-radio-button label="ALL">勾选平台都抓取</el-radio-button>
                <el-radio-button label="PRIORITY_STOP">按顺序命中即停止</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="自动补价">
              <el-switch v-model="settingForm.autoPriceEnabled" active-text="开启" inactive-text="关闭" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="自动提交">
              <el-switch v-model="settingForm.autoSubmitEnabled" active-text="开启" inactive-text="关闭" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="报价单抓取并发">
              <el-input-number v-model="settingForm.quotationCrawlConcurrency" :min="1" :max="50" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="补价并发">
              <el-input-number v-model="settingForm.priceConcurrency" :min="1" :max="50" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="请求超时毫秒">
              <el-input-number v-model="settingForm.requestTimeoutMs" :min="1000" :step="1000" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="失败重试次数">
              <el-input-number v-model="settingForm.retryTimes" :min="0" :max="20" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="最大处理报价单数">
              <el-input-number v-model="settingForm.maxQuotationProcessCount" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12" :xl="6">
            <el-form-item label="人工补价兜底">
              <el-switch v-model="settingForm.manualPriceFillEnabled" active-text="开启" inactive-text="关闭" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card shadow="hover" class="mt-[10px] platform-card">
      <template #header>
        <div class="section-title">
          <span>平台配置</span>
          <small>写入 user_part_crawler_platform_config，质量/品牌/区域/供应商均以 JSON 保存</small>
        </div>
      </template>

      <el-empty v-if="selectedPlatforms.length === 0" description="请先在全局设置里勾选至少一个平台" :image-size="90" />
      <el-tabs v-else v-model="activePlatformCode" type="border-card" @tab-change="handlePlatformChange">
        <el-tab-pane v-for="platform in selectedPlatforms" :key="platform.platformCode" :label="platform.platformName" :name="platform.platformCode">
          <div class="platform-grid">
            <aside class="platform-outline">
              <div class="outline-item active">1. 质量勾选</div>
              <div class="outline-item">2. 品牌过滤</div>
              <div class="outline-item">3. 供应商规则</div>
              <div class="outline-item">4. 区域优先级</div>
            </aside>

            <main class="platform-main" v-if="activeDraft">
              <el-card shadow="never" class="setting-block">
                <template #header>
                  <div class="block-title">
                    <span>质量勾选</span>
                    <small>勾选后，品牌列表会按质量关联关系过滤</small>
                  </div>
                </template>
                <el-checkbox-group v-model="activeDraft.qualityOriginIds" @change="handleQualityChange">
                  <el-checkbox v-for="item in qualityOptions" :key="item.qualityOriginId" :label="item.qualityOriginId">
                    {{ item.qualityName }}
                  </el-checkbox>
                </el-checkbox-group>
              </el-card>

              <el-card shadow="never" class="setting-block">
                <template #header>
                  <div class="block-title with-tools">
                    <div>
                      <span>品牌勾选</span>
                      <small>查询已勾选质量对应的品牌，分页勾选需要过滤的品牌</small>
                    </div>
                    <el-input v-model="brandQuery.brandName" placeholder="搜索品牌" clearable class="tool-input" @keyup.enter="loadBrands" @clear="loadBrands" />
                  </div>
                </template>
                <div class="bulk-toolbar">
                  <el-button size="small" type="primary" plain @click="toggleCurrentPageBrands(true)">本页全选</el-button>
                  <el-button size="small" plain @click="toggleCurrentPageBrands(false)">取消本页</el-button>
                  <span>本页 {{ currentPageCheckedBrandCount }}/{{ brandList.length }}，已选 {{ activeDraft.brandOriginIds.length }} 个品牌</span>
                </div>
                <el-table v-loading="brandLoading" :data="brandList" border row-key="brandOriginId">
                  <el-table-column width="78" align="center">
                    <template #header>
                      <el-checkbox
                        :model-value="isCurrentPageBrandAllChecked"
                        :indeterminate="isCurrentPageBrandIndeterminate"
                        @change="toggleCurrentPageBrands($event as boolean)"
                      />
                    </template>
                    <template #default="scope">
                      <el-checkbox :model-value="isBrandChecked(scope.row.brandOriginId)" @change="toggleBrand(scope.row, $event as boolean)" />
                    </template>
                  </el-table-column>
                  <el-table-column label="品牌名称" prop="brandName" min-width="160" />
                  <el-table-column label="品牌原始ID" prop="brandOriginId" min-width="160" />
                </el-table>
                <pagination
                  v-show="brandTotal > 0"
                  v-model:page="brandQuery.pageNum"
                  v-model:limit="brandQuery.pageSize"
                  :total="brandTotal"
                  :auto-scroll="false"
                  @pagination="loadBrandsKeepScroll"
                />
              </el-card>

              <el-card shadow="never" class="setting-block">
                <template #header>
                  <div class="block-title">
                    <div>
                      <span>供应商配置</span>
                      <small>供应商配置来源于已勾选品牌，每个品牌可关联多个供应商</small>
                    </div>
                  </div>
                </template>
                <el-alert v-if="brandSupplierRows.length === 0" title="请先在品牌勾选中选择需要配置供应商的品牌" type="info" show-icon :closable="false" class="mb-[10px]" />
                <el-table :data="pagedBrandSupplierRows" border>
                  <el-table-column label="品牌" min-width="150">
                    <template #default="scope">{{ scope.row.brandName || brandNameCache[scope.row.brandOriginId] || scope.row.brandOriginId }}</template>
                  </el-table-column>
                  <el-table-column label="已关联供应商" min-width="280">
                    <template #default="scope">
                      <div v-if="scope.row.suppliers.length > 0" class="supplier-tags">
                        <el-tag v-for="supplier in scope.row.suppliers.slice(0, 4)" :key="supplier.supplierOriginId" type="success" effect="plain">
                          {{ supplier.supplierName || supplierNameCache[supplier.supplierOriginId] || supplier.supplierOriginId }}
                        </el-tag>
                        <el-tag v-if="scope.row.suppliers.length > 4" type="info" effect="plain">+{{ scope.row.suppliers.length - 4 }}</el-tag>
                      </div>
                      <span v-else class="text-muted">暂未关联</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="加价/调货" width="160" align="center">
                    <template #default="scope">
                      <span v-if="scope.row.suppliers.length > 0">{{ scope.row.suppliers.length }} 条商家规则</span>
                      <span v-else class="text-muted">未配置</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="140" fixed="right" align="center">
                    <template #default="scope">
                      <el-button link type="primary" @click="openSupplierDialog(scope.row)">关联供应商</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <pagination
                  v-show="brandSupplierRows.length > supplierBrandPage.pageSize"
                  v-model:page="supplierBrandPage.pageNum"
                  v-model:limit="supplierBrandPage.pageSize"
                  :total="brandSupplierRows.length"
                  :auto-scroll="false"
                  @pagination="keepCurrentScroll"
                />
              </el-card>

              <el-card shadow="never" class="setting-block">
                <template #header>
                  <div class="block-title">
                    <span>区域配置</span>
                    <small>勾选区域后，可通过上移/下移调整抓取优先级</small>
                  </div>
                </template>
                <el-checkbox-group v-model="activeDraft.regionOriginIds">
                  <el-checkbox v-for="item in regionOptions" :key="item.regionOriginId" :label="item.regionOriginId">
                    {{ item.regionName }}
                  </el-checkbox>
                </el-checkbox-group>
                <div class="region-sort-list" v-if="activeDraft.regionOriginIds.length > 0">
                  <div v-for="(regionId, index) in activeDraft.regionOriginIds" :key="regionId" class="region-sort-item">
                    <span>{{ index + 1 }}. {{ regionNameMap[regionId] || regionId }}</span>
                    <div class="region-tools">
                      <el-input-number v-model="activeDraft.regionExtraDays[regionId]" :min="0" :max="365" size="small" controls-position="right" />
                      <el-button link type="primary" :disabled="index === 0" @click="moveRegion(index, -1)">上移</el-button>
                      <el-button link type="primary" :disabled="index === activeDraft.regionOriginIds.length - 1" @click="moveRegion(index, 1)">下移</el-button>
                    </div>
                  </div>
                </div>
              </el-card>
            </main>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      v-model="supplierDialog.visible"
      title="关联供应商"
      width="1280px"
      class="supplier-bind-dialog"
      align-center
      append-to-body
      destroy-on-close
    >
      <div class="supplier-dialog-head">
        <div>
          <div class="dialog-brand">{{ supplierDialog.brandName || supplierDialog.brandOriginId }}</div>
          <div class="dialog-tip">左侧查询未勾选供应商，右侧维护已勾选供应商的加价系数和调货天数。</div>
        </div>
      </div>
      <div class="supplier-transfer-layout">
        <section class="transfer-panel">
          <div class="transfer-panel-head">
            <div>
              <span>未勾选供应商</span>
              <small>双击或勾选后点击右箭头加入</small>
            </div>
            <el-tag type="info" effect="plain">共 {{ supplierDialog.total }} 条</el-tag>
          </div>
          <div class="dialog-search-row">
            <el-input
              v-model="supplierDialog.query.supplierName"
              placeholder="可输入：宝鑫行 广全 奕宝 企宝 粤翔 至诚 德曼 影富"
              clearable
              @keyup.enter="loadDialogSuppliers"
              @clear="loadDialogSuppliers"
            />
            <el-button type="primary" :loading="supplierDialog.loading" @click="loadDialogSuppliers">搜索</el-button>
          </div>
          <div class="transfer-table-wrap">
            <el-table
              v-loading="supplierDialog.loading"
              :data="unselectedSupplierRows"
              border
              row-key="supplierOriginId"
              height="100%"
              @selection-change="handleAvailableSelectionChange"
              @row-dblclick="addSupplierFromRow"
            >
              <el-table-column type="selection" width="48" align="center" />
              <el-table-column label="供应商名称" min-width="220" show-overflow-tooltip>
                <template #default="scope">{{ scope.row.supplierName || supplierNameCache[scope.row.supplierOriginId] || '-' }}</template>
              </el-table-column>
            </el-table>
          </div>
          <pagination
            v-show="supplierDialog.total > 0"
            class="dialog-pagination"
            v-model:page="supplierDialog.query.pageNum"
            v-model:limit="supplierDialog.query.pageSize"
            :total="supplierDialog.total"
            :auto-scroll="false"
            @pagination="loadDialogSuppliers"
          />
        </section>

        <div class="transfer-actions">
          <el-button type="primary" icon="ArrowRight" circle :disabled="supplierDialog.leftCheckedSupplierIds.length === 0" @click="addCheckedSuppliers" />
          <el-button type="primary" plain icon="ArrowLeft" circle :disabled="supplierDialog.rightCheckedSupplierIds.length === 0" @click="removeCheckedSuppliers" />
        </div>

        <section class="transfer-panel selected-panel">
          <div class="transfer-panel-head">
            <div>
              <span>已勾选供应商</span>
              <small>双击可取消，右侧字段与商家绑定</small>
            </div>
            <el-tag type="success" effect="plain">已选 {{ supplierDialog.supplierConfigs.length }} 个</el-tag>
          </div>
          <div class="transfer-table-wrap selected-table-wrap">
            <el-table
              :data="supplierDialog.supplierConfigs"
              border
              row-key="supplierOriginId"
              height="100%"
              @selection-change="handleSelectedSelectionChange"
              @row-dblclick="removeSupplierFromRow"
            >
              <el-table-column type="selection" width="48" align="center" />
              <el-table-column label="供应商名称" min-width="180" show-overflow-tooltip>
                <template #default="scope">{{ scope.row.supplierName || supplierNameCache[scope.row.supplierOriginId] || '-' }}</template>
              </el-table-column>
              <el-table-column label="加价系数" width="150">
                <template #default="scope">
                  <el-input-number v-model="scope.row.markupRate" :min="0" :step="0.01" :precision="2" controls-position="right" />
                </template>
              </el-table-column>
              <el-table-column label="调货天数" width="140">
                <template #default="scope">
                  <el-input-number v-model="scope.row.transferDays" :min="0" :max="365" controls-position="right" />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </div>
      <template #footer>
        <el-button @click="supplierDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveSupplierDialog">保存关联</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="KaisiWorkbenchSettings">
import { ComponentInternalInstance } from 'vue';
import { listPartCrawlerPlatformOptions } from '@/api/kaisi/base-config';
import {
  getKaisiWorkbenchSetting,
  listKaisiSettingBrands,
  listKaisiSettingQualities,
  listKaisiSettingRegions,
  listKaisiSettingSuppliers,
  saveKaisiWorkbenchSetting
} from '@/api/kaisi/workbench';
import {
  PartCrawlerPlatformBrandVO,
  PartCrawlerPlatformQualityVO,
  PartCrawlerPlatformRegionVO,
  PartCrawlerPlatformSupplierVO,
  PartCrawlerPlatformVO
} from '@/api/kaisi/base-config/types';
import { KaisiWorkbenchSettingForm, UserPlatformSettingVO } from '@/api/kaisi/workbench/types';

interface PlatformDraft {
  id?: number;
  platformId?: number;
  platformCode: string;
  defaultCity?: string;
  priceAdvantageRate: number;
  singleSkuMaxCrawlCount: number;
  qualityOriginIds: string[];
  brandOriginIds: string[];
  regionOriginIds: string[];
  regionExtraDays: Record<string, number>;
  supplierConfigs: SupplierConfig[];
  defaultMarkupRate: number;
  defaultTransferDays: number;
  crawlStrategyStopOnHit: boolean;
}

interface SupplierConfig {
  brandOriginId: string;
  brandName?: string;
  suppliers: SupplierBindConfig[];
}

interface SupplierBindConfig {
  supplierOriginId: string;
  supplierName?: string;
  markupRate: number;
  transferDays: number;
}

interface SupplierDialogState {
  visible: boolean;
  loading: boolean;
  brandOriginId: string;
  brandName?: string;
  supplierConfigs: SupplierBindConfig[];
  leftCheckedSupplierIds: string[];
  rightCheckedSupplierIds: string[];
  total: number;
  query: {
    pageNum: number;
    pageSize: number;
    supplierName: string;
  };
}

const { proxy } = getCurrentInstance() as ComponentInternalInstance;

const loading = ref(false);
const saveLoading = ref(false);
const platformOptions = ref<PartCrawlerPlatformVO[]>([]);
const activePlatformCode = ref('');
const platformDraftMap = reactive<Record<string, PlatformDraft>>({});

const qualityOptions = ref<PartCrawlerPlatformQualityVO[]>([]);
const regionOptions = ref<PartCrawlerPlatformRegionVO[]>([]);
const supplierOptions = ref<PartCrawlerPlatformSupplierVO[]>([]);
const brandList = ref<PartCrawlerPlatformBrandVO[]>([]);
const brandTotal = ref(0);
const brandLoading = ref(false);
const brandNameCache = reactive<Record<string, string>>({});
const supplierNameCache = reactive<Record<string, string>>({});

const brandQuery = reactive({ pageNum: 1, pageSize: 10, brandName: '' });
const supplierBrandPage = reactive({ pageNum: 1, pageSize: 10 });
const supplierDialog = reactive<SupplierDialogState>({
  visible: false,
  loading: false,
  brandOriginId: '',
  brandName: '',
  supplierConfigs: [],
  leftCheckedSupplierIds: [],
  rightCheckedSupplierIds: [],
  total: 0,
  query: {
    pageNum: 1,
    pageSize: 10,
    supplierName: ''
  }
});

const settingForm = reactive<KaisiWorkbenchSettingForm>({
  selectedPlatformCodes: [],
  crawlStrategyType: 'ALL',
  autoPriceEnabled: true,
  autoSubmitEnabled: false,
  quotationCrawlConcurrency: 1,
  priceConcurrency: 1,
  requestTimeoutMs: 30000,
  retryTimes: 3,
  maxQuotationProcessCount: 0,
  manualPriceFillEnabled: false,
  platformConfigs: []
});

const selectedPlatforms = computed(() => platformOptions.value.filter((item) => settingForm.selectedPlatformCodes.includes(item.platformCode)));
const activePlatform = computed(() => selectedPlatforms.value.find((item) => item.platformCode === activePlatformCode.value));
const activeDraft = computed(() => (activePlatformCode.value ? platformDraftMap[activePlatformCode.value] : undefined));
const regionNameMap = computed(() => Object.fromEntries(regionOptions.value.map((item) => [item.regionOriginId, item.regionName])));
const brandSupplierRows = computed(() => {
  if (!activeDraft.value) return [];
  return activeDraft.value.supplierConfigs.filter((item) => activeDraft.value?.brandOriginIds.includes(item.brandOriginId));
});
const currentPageCheckedBrandCount = computed(() => brandList.value.filter((item) => isBrandChecked(item.brandOriginId)).length);
const isCurrentPageBrandAllChecked = computed(() => brandList.value.length > 0 && currentPageCheckedBrandCount.value === brandList.value.length);
const isCurrentPageBrandIndeterminate = computed(() => currentPageCheckedBrandCount.value > 0 && currentPageCheckedBrandCount.value < brandList.value.length);
const pagedBrandSupplierRows = computed(() => {
  const start = (supplierBrandPage.pageNum - 1) * supplierBrandPage.pageSize;
  return brandSupplierRows.value.slice(start, start + supplierBrandPage.pageSize);
});
const unselectedSupplierRows = computed(() => {
  const selectedIds = new Set(supplierDialog.supplierConfigs.map((item) => item.supplierOriginId));
  return supplierOptions.value
    .filter((item) => !selectedIds.has(item.supplierOriginId))
    .map((item) => ({ ...item, supplierName: item.supplierName || supplierNameCache[item.supplierOriginId] }));
});

const keepScroll = async (runner?: () => Promise<void> | void) => {
  const top = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
  if (runner) {
    await runner();
  }
  await nextTick();
  window.scrollTo({ top, behavior: 'auto' });
};

const keepCurrentScroll = () => keepScroll();
const loadBrandsKeepScroll = () => keepScroll(loadBrands);

const parseJsonArray = (text?: string): string[] => {
  if (!text) return [];
  try {
    const value = JSON.parse(text);
    return Array.isArray(value) ? value.map(String) : [];
  } catch {
    return [];
  }
};

const parseJsonObject = (text?: string): Record<string, number> => {
  if (!text) return {};
  try {
    const value = JSON.parse(text);
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
};

const parseSupplierConfigs = (text?: string): SupplierConfig[] => {
  if (!text) return [];
  try {
    const value = JSON.parse(text);
    if (!Array.isArray(value)) return [];
    return value.map((item) => {
      const brandOriginId = String(item.brandOriginId || '');
      const brandName = item.brandName;
      const suppliers = Array.isArray(item.suppliers)
        ? item.suppliers.map((supplier: any) => ({
          supplierOriginId: String(supplier.supplierOriginId || ''),
          supplierName: supplier.supplierName || supplierNameCache[String(supplier.supplierOriginId || '')],
          markupRate: Number(supplier.markupRate || 0),
          transferDays: Number(supplier.transferDays || 0)
        })).filter((supplier: SupplierBindConfig) => supplier.supplierOriginId)
        : (Array.isArray(item.supplierOriginIds) ? item.supplierOriginIds.map((supplierOriginId: string) => ({
          supplierOriginId: String(supplierOriginId),
          supplierName: supplierNameCache[String(supplierOriginId)],
          markupRate: Number(item.markupRate || 0),
          transferDays: Number(item.transferDays || 0)
        })) : []);
      return { brandOriginId, brandName, suppliers };
    }).filter((item) => item.brandOriginId);
  } catch {
    return [];
  }
};

const createDraft = (platform: PartCrawlerPlatformVO, source?: UserPlatformSettingVO): PlatformDraft => ({
  id: source?.id,
  platformId: platform.id,
  platformCode: platform.platformCode,
  defaultCity: source?.defaultCity || '',
  priceAdvantageRate: source?.priceAdvantageRate ?? 5,
  singleSkuMaxCrawlCount: source?.singleSkuMaxCrawlCount ?? 0,
  qualityOriginIds: parseJsonArray(source?.qualityOriginIdsJson),
  brandOriginIds: parseJsonArray(source?.brandOriginIdsJson),
  regionOriginIds: parseJsonArray(source?.regionOriginIdsJson),
  regionExtraDays: parseJsonObject(source?.regionExtraDaysJson),
  supplierConfigs: parseSupplierConfigs(source?.supplierConfigsJson),
  defaultMarkupRate: source?.defaultMarkupRate ?? 0,
  defaultTransferDays: source?.defaultTransferDays ?? 0,
  crawlStrategyStopOnHit: source?.crawlStrategyStopOnHit ?? false
});

const ensureDraft = (platform: PartCrawlerPlatformVO) => {
  if (!platformDraftMap[platform.platformCode]) {
    platformDraftMap[platform.platformCode] = createDraft(platform);
  }
};

const loadPlatformOptions = async () => {
  const { data } = await listPartCrawlerPlatformOptions();
  platformOptions.value = data || [];
};

const loadSetting = async () => {
  loading.value = true;
  try {
    await loadPlatformOptions();
    const { data } = await getKaisiWorkbenchSetting();
    Object.assign(settingForm, {
      selectedPlatformCodes: data?.selectedPlatformCodes || [],
      crawlStrategyType: data?.crawlStrategyType || 'ALL',
      autoPriceEnabled: data?.autoPriceEnabled ?? true,
      autoSubmitEnabled: data?.autoSubmitEnabled ?? false,
      quotationCrawlConcurrency: data?.quotationCrawlConcurrency || 1,
      priceConcurrency: data?.priceConcurrency || 1,
      requestTimeoutMs: data?.requestTimeoutMs || 30000,
      retryTimes: data?.retryTimes ?? 3,
      maxQuotationProcessCount: data?.maxQuotationProcessCount ?? 0,
      manualPriceFillEnabled: data?.manualPriceFillEnabled ?? false,
      platformConfigs: data?.platformConfigs || []
    });
    (data?.platformConfigs || []).forEach((item) => {
      const platform = platformOptions.value.find((option) => option.platformCode === item.platformCode);
      if (platform) platformDraftMap[item.platformCode] = createDraft(platform, item);
    });
    selectedPlatforms.value.forEach((platform) => {
      ensureDraft(platform);
      syncSupplierConfigs(platformDraftMap[platform.platformCode]);
    });
    activePlatformCode.value = settingForm.selectedPlatformCodes[0] || '';
    await reloadActiveOptions();
  } finally {
    loading.value = false;
  }
};

const reloadActiveOptions = async () => {
  if (!activePlatform.value) return;
  ensureDraft(activePlatform.value);
  const platformId = activePlatform.value.id;
  const [qualities, regions] = await Promise.all([listKaisiSettingQualities(platformId), listKaisiSettingRegions(platformId)]);
  qualityOptions.value = qualities.data || [];
  regionOptions.value = regions.data || [];
  syncSupplierConfigs(activeDraft.value);
  await Promise.all([loadBrands(), loadSupplierNameCache()]);
};

const loadBrands = async () => {
  if (!activePlatform.value || !activeDraft.value) return;
  brandLoading.value = true;
  try {
    const res: any = await listKaisiSettingBrands({
      platformId: activePlatform.value.id,
      qualityOriginIds: JSON.stringify(activeDraft.value.qualityOriginIds),
      brandName: brandQuery.brandName,
      pageNum: brandQuery.pageNum,
      pageSize: brandQuery.pageSize
    });
    brandList.value = res.rows || [];
    brandTotal.value = res.total || 0;
    brandList.value.forEach((item) => (brandNameCache[item.brandOriginId] = item.brandName));
  } finally {
    brandLoading.value = false;
  }
};

const loadSupplierNameCache = async () => {
  if (!activePlatform.value) return;
  const res: any = await listKaisiSettingSuppliers({
    platformId: activePlatform.value.id,
    pageNum: 1,
    pageSize: 1000
  });
  (res.rows || []).forEach((item: PartCrawlerPlatformSupplierVO) => (supplierNameCache[item.supplierOriginId] = item.supplierName));
};

const loadDialogSuppliers = async () => {
  if (!activePlatform.value) return;
  supplierDialog.loading = true;
  try {
    const res: any = await listKaisiSettingSuppliers({
      platformId: activePlatform.value.id,
      supplierName: supplierDialog.query.supplierName,
      pageNum: supplierDialog.query.pageNum,
      pageSize: supplierDialog.query.pageSize
    });
    supplierOptions.value = res.rows || [];
    supplierDialog.total = res.total || 0;
    supplierOptions.value.forEach((item) => (supplierNameCache[item.supplierOriginId] = item.supplierName));
  } finally {
    supplierDialog.loading = false;
  }
};

const handlePlatformChange = async () => {
  await keepScroll(async () => {
    brandQuery.pageNum = 1;
    supplierBrandPage.pageNum = 1;
    await reloadActiveOptions();
  });
};

const handleQualityChange = async () => {
  await keepScroll(async () => {
    brandQuery.pageNum = 1;
    await loadBrands();
  });
};

const isBrandChecked = (brandOriginId: string) => activeDraft.value?.brandOriginIds.includes(brandOriginId) || false;

const ensureSupplierConfig = (brandOriginId: string, brandName?: string): SupplierConfig | undefined => {
  if (!activeDraft.value || !brandOriginId) return undefined;
  let config = activeDraft.value.supplierConfigs.find((item) => item.brandOriginId === brandOriginId);
  if (!config) {
    config = { brandOriginId, brandName: brandName || brandNameCache[brandOriginId], suppliers: [] };
    activeDraft.value.supplierConfigs.push(config);
  }
  if (brandName) {
    config.brandName = brandName;
    brandNameCache[brandOriginId] = brandName;
  }
  return config;
};

const syncSupplierConfigs = (draft?: PlatformDraft) => {
  if (!draft) return;
  const selectedBrandIds = new Set(draft.brandOriginIds);
  draft.supplierConfigs = draft.supplierConfigs.filter((item) => selectedBrandIds.has(item.brandOriginId));
  draft.brandOriginIds.forEach((brandOriginId) => {
    if (!draft.supplierConfigs.some((item) => item.brandOriginId === brandOriginId)) {
      draft.supplierConfigs.push({ brandOriginId, brandName: brandNameCache[brandOriginId], suppliers: [] });
    }
  });
};

const toggleBrand = (row: PartCrawlerPlatformBrandVO, checked: boolean) => {
  if (!activeDraft.value) return;
  brandNameCache[row.brandOriginId] = row.brandName;
  if (checked && !activeDraft.value.brandOriginIds.includes(row.brandOriginId)) {
    activeDraft.value.brandOriginIds.push(row.brandOriginId);
    ensureSupplierConfig(row.brandOriginId, row.brandName);
  }
  if (!checked) {
    activeDraft.value.brandOriginIds = activeDraft.value.brandOriginIds.filter((item) => item !== row.brandOriginId);
    activeDraft.value.supplierConfigs = activeDraft.value.supplierConfigs.filter((item) => item.brandOriginId !== row.brandOriginId);
  }
};

const toggleCurrentPageBrands = (checked: boolean) => {
  brandList.value.forEach((row) => toggleBrand(row, checked));
  syncSupplierConfigs(activeDraft.value);
};

const openSupplierDialog = async (row: SupplierConfig) => {
  supplierDialog.brandOriginId = row.brandOriginId;
  supplierDialog.brandName = row.brandName || brandNameCache[row.brandOriginId] || row.brandOriginId;
  supplierDialog.supplierConfigs = (row.suppliers || []).map((item) => ({ ...item }));
  supplierDialog.leftCheckedSupplierIds = [];
  supplierDialog.rightCheckedSupplierIds = [];
  supplierDialog.query.pageNum = 1;
  supplierDialog.query.pageSize = 10;
  supplierDialog.query.supplierName = '';
  supplierDialog.visible = true;
  await loadDialogSuppliers();
};

const getDialogSupplierConfig = (supplierOriginId: string) => supplierDialog.supplierConfigs.find((item) => item.supplierOriginId === supplierOriginId);

const handleAvailableSelectionChange = (rows: PartCrawlerPlatformSupplierVO[]) => {
  supplierDialog.leftCheckedSupplierIds = rows.map((item) => item.supplierOriginId);
};

const handleSelectedSelectionChange = (rows: SupplierBindConfig[]) => {
  supplierDialog.rightCheckedSupplierIds = rows.map((item) => item.supplierOriginId);
};

const addSupplierFromRow = (row: PartCrawlerPlatformSupplierVO) => {
  supplierNameCache[row.supplierOriginId] = row.supplierName;
  if (!getDialogSupplierConfig(row.supplierOriginId)) {
    supplierDialog.supplierConfigs.push({ supplierOriginId: row.supplierOriginId, supplierName: row.supplierName, markupRate: 0, transferDays: 0 });
  }
};

const addCheckedSuppliers = () => {
  const checkedIds = new Set(supplierDialog.leftCheckedSupplierIds);
  supplierOptions.value.filter((item) => checkedIds.has(item.supplierOriginId)).forEach(addSupplierFromRow);
  supplierDialog.leftCheckedSupplierIds = [];
};

const removeSupplierFromRow = (row: SupplierBindConfig) => {
  supplierDialog.supplierConfigs = supplierDialog.supplierConfigs.filter((item) => item.supplierOriginId !== row.supplierOriginId);
  supplierDialog.rightCheckedSupplierIds = supplierDialog.rightCheckedSupplierIds.filter((item) => item !== row.supplierOriginId);
};

const removeCheckedSuppliers = () => {
  const checkedIds = new Set(supplierDialog.rightCheckedSupplierIds);
  supplierDialog.supplierConfigs = supplierDialog.supplierConfigs.filter((item) => !checkedIds.has(item.supplierOriginId));
  supplierDialog.rightCheckedSupplierIds = [];
};

const saveSupplierDialog = () => {
  const config = ensureSupplierConfig(supplierDialog.brandOriginId, supplierDialog.brandName);
  if (!config) return;
  config.suppliers = supplierDialog.supplierConfigs.map((item) => ({
    ...item,
    supplierName: item.supplierName || supplierNameCache[item.supplierOriginId]
  }));
  supplierDialog.visible = false;
};

const moveRegion = (index: number, offset: number) => {
  if (!activeDraft.value) return;
  const target = index + offset;
  const rows = activeDraft.value.regionOriginIds;
  [rows[index], rows[target]] = [rows[target], rows[index]];
};

const buildPlatformPayload = () => selectedPlatforms.value.map((platform) => {
  ensureDraft(platform);
  const draft = platformDraftMap[platform.platformCode];
  return {
    id: draft.id,
    platformId: platform.id,
    platformCode: platform.platformCode,
    defaultCity: draft.defaultCity,
    priceAdvantageRate: draft.priceAdvantageRate,
    singleSkuMaxCrawlCount: draft.singleSkuMaxCrawlCount,
    qualityOriginIdsJson: JSON.stringify(draft.qualityOriginIds),
    brandOriginIdsJson: JSON.stringify(draft.brandOriginIds),
    regionOriginIdsJson: JSON.stringify(draft.regionOriginIds),
    regionExtraDaysJson: JSON.stringify(draft.regionExtraDays),
    supplierConfigsJson: JSON.stringify(draft.supplierConfigs
      .filter((item) => draft.brandOriginIds.includes(item.brandOriginId))
      .map((item) => ({ ...item, brandName: item.brandName || brandNameCache[item.brandOriginId] }))),
    defaultMarkupRate: draft.defaultMarkupRate,
    defaultTransferDays: draft.defaultTransferDays,
    crawlStrategyType: 'FULL_SELECTED',
    crawlStrategyStopOnHit: settingForm.crawlStrategyType === 'PRIORITY_STOP'
  };
});

const handleSave = async () => {
  saveLoading.value = true;
  try {
    await saveKaisiWorkbenchSetting({ ...settingForm, platformConfigs: buildPlatformPayload() });
    proxy?.$modal.msgSuccess('工作台基础配置已保存');
    await loadSetting();
  } finally {
    saveLoading.value = false;
  }
};

watch(
  () => settingForm.selectedPlatformCodes.slice(),
  async () => {
    selectedPlatforms.value.forEach((platform) => {
      ensureDraft(platform);
      syncSupplierConfigs(platformDraftMap[platform.platformCode]);
    });
    if (!settingForm.selectedPlatformCodes.includes(activePlatformCode.value)) {
      activePlatformCode.value = settingForm.selectedPlatformCodes[0] || '';
      await keepScroll(reloadActiveOptions);
    }
  }
);

onMounted(loadSetting);
</script>

<style scoped lang="scss">
.kaisi-workbench-settings {
  .setting-hero {
    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      background: linear-gradient(135deg, #f7fbff 0%, #eef6f2 100%);
    }
  }

  .hero-kicker {
    color: #409eff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
  }

  .hero-title {
    margin-top: 4px;
    color: #1f2d3d;
    font-size: 22px;
    font-weight: 700;
  }

  .hero-desc {
    margin-top: 6px;
    color: #606266;
    line-height: 1.6;
  }

  .section-title,
  .block-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-weight: 700;
    color: #303133;

    small {
      color: #909399;
      font-weight: 400;
    }
  }

  .with-tools {
    align-items: flex-start;
  }

  .tool-input {
    width: 220px;
  }

  .bulk-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    color: #909399;
    font-size: 12px;
  }

  .supplier-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .text-muted {
    color: #a8abb2;
  }

  .supplier-dialog-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
  }

  .dialog-brand {
    color: #303133;
    font-size: 16px;
    font-weight: 700;
  }

  .dialog-tip {
    margin-top: 4px;
    color: #909399;
    font-size: 12px;
  }

  .dialog-form-inline,
  .dialog-search-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .dialog-form-inline {
    color: #606266;
    font-size: 12px;
    white-space: nowrap;
  }

  .dialog-search-row {
    margin-bottom: 10px;

    :deep(.el-input) {
      flex: 1;
    }
  }

  .supplier-transfer-layout {
    display: grid;
    grid-template-columns: minmax(360px, 0.92fr) 56px minmax(480px, 1.08fr);
    gap: 14px;
    align-items: stretch;
    height: min(58vh, 560px);
    min-height: 460px;
  }

  .transfer-panel {
    display: flex;
    min-height: 0;
    min-width: 0;
    flex-direction: column;
    padding: 14px;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    background: #ffffff;
  }

  .transfer-panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
    color: #303133;
    font-weight: 700;

    small {
      color: #909399;
      font-weight: 400;
    }
  }

  .transfer-table-wrap {
    min-height: 0;
    flex: 1;
    overflow: hidden;
  }

  .dialog-pagination {
    margin-top: 12px;
    padding: 0;

    :deep(.pagination-container) {
      height: auto;
      margin: 0;
      padding: 0;
    }
  }

  .selected-panel {
    background: #fbfdff;
  }

  .selected-table-wrap {
    margin-top: 0;
  }

  .transfer-actions {
    display: flex;
    align-items: center;
    flex-direction: column;
    gap: 12px;
    justify-content: center;

    .el-button + .el-button {
      margin-left: 0;
    }
  }

  .platform-grid {
    display: grid;
    grid-template-columns: 180px minmax(0, 1fr);
    gap: 14px;
  }

  .platform-outline {
    border-right: 1px solid #ebeef5;
    padding-right: 12px;
  }

  .outline-item {
    margin-bottom: 8px;
    padding: 9px 10px;
    border-radius: 8px;
    color: #606266;
    background: #f7f8fa;
  }

  .outline-item.active {
    color: #1f5fbf;
    background: #ecf5ff;
    font-weight: 700;
  }

  .setting-block + .setting-block {
    margin-top: 12px;
  }

  .region-sort-list {
    margin-top: 12px;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    overflow: hidden;
  }

  .region-sort-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border-bottom: 1px solid #ebeef5;
  }

  .region-sort-item:last-child {
    border-bottom: 0;
  }

  .region-tools {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  :deep(.el-input-number) {
    width: 170px;
  }

  @media (max-width: 960px) {
    .setting-hero :deep(.el-card__body) {
      align-items: flex-start;
      flex-direction: column;
    }

    .platform-grid {
      grid-template-columns: 1fr;
    }

    .platform-outline {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      border-right: 0;
      padding-right: 0;
      gap: 8px;
    }

    .bulk-toolbar,
    .supplier-dialog-head,
    .dialog-form-inline,
    .dialog-search-row {
      align-items: stretch;
      flex-direction: column;
    }

    .supplier-transfer-layout {
      height: auto;
      min-height: 0;
      grid-template-columns: 1fr;
    }

    .transfer-table-wrap {
      height: 320px;
      flex: none;
    }

    .transfer-actions {
      flex-direction: row;
      justify-content: center;
    }
  }
}

:deep(.supplier-bind-dialog) {
  max-width: calc(100vw - 48px);
}

:deep(.supplier-bind-dialog .el-dialog__body),
:deep(.el-dialog.supplier-bind-dialog .el-dialog__body) {
  max-height: calc(90vh - 154px);
  padding: 16px 24px 18px;
  overflow: hidden;
}

:deep(.supplier-bind-dialog .el-dialog__footer),
:deep(.el-dialog.supplier-bind-dialog .el-dialog__footer) {
  padding: 12px 24px 18px;
  border-top: 1px solid #ebeef5;
}

:deep(.supplier-bind-dialog .el-table__row) {
  cursor: pointer;
}

:deep(.supplier-bind-dialog .el-input-number) {
  width: 120px;
}

.supplier-bind-dialog {
  max-width: calc(100vw - 48px);
}

.supplier-bind-dialog :deep(.el-dialog__body) {
  max-height: calc(90vh - 154px);
  padding: 16px 24px 18px;
  overflow: hidden;
}

.supplier-bind-dialog :deep(.el-dialog__footer) {
  padding: 12px 24px 18px;
  border-top: 1px solid #ebeef5;
}

.supplier-dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.dialog-brand {
  color: #303133;
  font-size: 16px;
  font-weight: 700;
}

.dialog-tip {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.dialog-search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.dialog-search-row :deep(.el-input) {
  flex: 1;
}

.supplier-transfer-layout {
  display: flex;
  align-items: stretch;
  gap: 14px;
  height: min(58vh, 560px);
  min-height: 460px;
}

.supplier-transfer-layout .transfer-panel {
  display: flex;
  min-width: 0;
  min-height: 0;
  flex: 1 1 0;
  flex-direction: column;
  padding: 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #ffffff;
}

.supplier-transfer-layout .selected-panel {
  flex: 1.18 1 0;
  background: #fbfdff;
}

.transfer-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  color: #303133;
  font-weight: 700;
}

.transfer-panel-head small {
  color: #909399;
  font-weight: 400;
}

.transfer-table-wrap {
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.dialog-pagination {
  margin-top: 12px;
  padding: 0;
}

.dialog-pagination :deep(.pagination-container) {
  height: auto;
  margin: 0;
  padding: 0;
}

.supplier-transfer-layout .transfer-actions {
  display: flex;
  align-items: center;
  flex: 0 0 56px;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.supplier-transfer-layout .transfer-actions .el-button + .el-button {
  margin-left: 0;
}

.supplier-bind-dialog :deep(.el-table__row) {
  cursor: pointer;
}

.supplier-bind-dialog :deep(.el-input-number) {
  width: 120px;
}

@media (max-width: 720px) {
  .supplier-dialog-head,
  .dialog-search-row {
    align-items: stretch;
    flex-direction: column;
  }

  .supplier-transfer-layout {
    height: auto;
    min-height: 0;
    flex-direction: column;
  }

  .transfer-table-wrap {
    height: 320px;
    flex: none;
  }

  .supplier-transfer-layout .transfer-actions {
    flex: none;
    flex-direction: row;
    justify-content: center;
  }
}
</style>
