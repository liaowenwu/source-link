export interface KaisiTimelineVO {
  taskNo: string;
  eventType: string;
  eventLevel: string;
  displayTitle: string;
  displayContent: string;
  quotationId: string;
  storeId: string;
  createTime: string;
}

export interface KaisiQuotationVO {
  quotationId: string;
  inquiryId: string;
  storeId: string;
  statusIdDesc: string;
  flowStatus: string;
  processStatus: string;
  currentNodeCode: string;
  currentNodeName: string;
  itemCount: number;
  quotedItemCount: number;
  unquoteItemCount: number;
  submittedItemCount: number;
  exceptionItemCount: number;
  manualPriceFillEnabled: boolean;
  autoSubmitEnabled: boolean;
  needAlert: boolean;
  assignedUserId: number;
  lastMessage: string;
  errorMessage: string;
  lastLogTime: string;
}

export interface KaisiDashboardVO {
  taskNo: string;
  serviceStatus: string;
  currentMessage: string;
  todayCatchCount: number;
  todayPriceCount: number;
  todaySubmitCount: number;
  runningSeconds: number;
  lastPollTime: string;
  latestCatchTime: string;
  waitPriceCount: number;
  waitSubmitCount: number;
  timeline: KaisiTimelineVO[];
  alertTimeline: KaisiTimelineVO[];
  quickQuotations: KaisiQuotationVO[];
}

export interface KaisiQuoteItemVO {
  id: number;
  quotationId: string;
  storeId: string;
  onlineOrderItemId: string;
  resolveResultId: string;
  partsNum: string;
  partsName: string;
  brandName: string;
  partsBrandQuality: string;
  storeServiceArea: string;
  quantity: number;
  suggestedPrice: number;
  finalPrice: number;
  itemProcessStatus: string;
  unmatchedReason: string;
  remark: string;
}

export interface KaisiQuotationQuery {
  pageNum: number;
  pageSize: number;
  quotationId?: string;
  inquiryId?: string;
  storeId?: string;
  flowStatus?: string;
  processStatus?: string;
  scene?: string;
  manualPriceFillEnabled?: boolean;
  beginTime?: string;
  endTime?: string;
}

export interface KaisiManualPriceForm {
  itemId: number;
  quotationId: string;
  storeId: string;
  finalPrice: number;
  unmatchedReason?: string;
  remark?: string;
}

export interface KaisiHistoryPartVO {
  partsNum: string;
  partsName: string;
  brandName: string;
  partsBrandQuality: string;
  quoteTimes: number;
  avgFinalPrice: number;
  latestQuoteTime: string;
}

export interface KaisiPriceTrendPointVO {
  quotationId: string;
  storeId: string;
  partsNum: string;
  partsName: string;
  brandName: string;
  partsBrandQuality: string;
  suggestedPrice: number;
  finalPrice: number;
  quoteTime: string;
}

export interface UserPlatformSettingVO {
  id?: number;
  userId?: number;
  platformId?: number;
  platformCode: string;
  defaultCity?: string;
  priceAdvantageRate?: number;
  regionExtraDaysJson?: string;
  singleSkuMaxCrawlCount?: number;
  qualityOriginIdsJson?: string;
  brandOriginIdsJson?: string;
  regionOriginIdsJson?: string;
  supplierConfigsJson?: string;
  defaultMarkupRate?: number;
  defaultTransferDays?: number;
  crawlStrategyType?: string;
  crawlStrategySelectedPlatformCodesJson?: string;
  crawlStrategyPriorityPlatformCodesJson?: string;
  crawlStrategyStopOnHit?: boolean;
}

export interface KaisiWorkbenchSettingVO {
  id?: number;
  userId?: number;
  selectedPlatformCodes: string[];
  crawlStrategyType: string;
  autoPriceEnabled: boolean;
  autoSubmitEnabled: boolean;
  quotationCrawlConcurrency: number;
  priceConcurrency: number;
  requestTimeoutMs: number;
  retryTimes: number;
  maxQuotationProcessCount: number;
  manualPriceFillEnabled: boolean;
  platformConfigs: UserPlatformSettingVO[];
}

export interface KaisiWorkbenchSettingForm extends KaisiWorkbenchSettingVO {}
