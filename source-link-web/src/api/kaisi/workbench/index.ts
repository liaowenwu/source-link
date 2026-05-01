import request from '@/utils/request';
import { AxiosPromise } from 'axios';
import {
  KaisiDashboardVO,
  KaisiHistoryPartVO,
  KaisiManualPriceForm,
  KaisiPriceTrendPointVO,
  KaisiQuotationQuery,
  KaisiQuotationVO,
  KaisiQuoteItemVO,
  KaisiTimelineVO,
  KaisiWorkbenchSettingForm,
  KaisiWorkbenchSettingVO
} from './types';
import {
  PartCrawlerPlatformBrandVO,
  PartCrawlerPlatformQualityVO,
  PartCrawlerPlatformRegionVO,
  PartCrawlerPlatformSupplierVO
} from '@/api/kaisi/base-config/types';

// 查询工作台首页
export const getKaisiDashboard = (): AxiosPromise<KaisiDashboardVO> => {
  return request({
    url: '/kaisi/workbench/dashboard',
    method: 'get'
  });
};

// 查询工作台设置
export const getKaisiWorkbenchSetting = (): AxiosPromise<KaisiWorkbenchSettingVO> => {
  return request({
    url: '/kaisi/workbench/settings',
    method: 'get'
  });
};

// 保存工作台设置
export const saveKaisiWorkbenchSetting = (data: KaisiWorkbenchSettingForm) => {
  return request({
    url: '/kaisi/workbench/settings',
    method: 'put',
    data
  });
};

// 查询平台质量选项
export const listKaisiSettingQualities = (platformId: number): AxiosPromise<PartCrawlerPlatformQualityVO[]> => {
  return request({
    url: '/kaisi/workbench/settings/platform-qualities',
    method: 'get',
    params: { platformId }
  });
};

// 查询平台品牌选项
export const listKaisiSettingBrands = (params: {
  platformId: number;
  qualityOriginIds?: string;
  brandName?: string;
  pageNum: number;
  pageSize: number;
}): AxiosPromise<PartCrawlerPlatformBrandVO[]> => {
  return request({
    url: '/kaisi/workbench/settings/platform-brands',
    method: 'get',
    params
  });
};

// 查询平台区域选项
export const listKaisiSettingRegions = (platformId: number): AxiosPromise<PartCrawlerPlatformRegionVO[]> => {
  return request({
    url: '/kaisi/workbench/settings/platform-regions',
    method: 'get',
    params: { platformId }
  });
};

// 查询平台供应商选项
export const listKaisiSettingSuppliers = (params: {
  platformId: number;
  supplierName?: string;
  pageNum: number;
  pageSize: number;
}): AxiosPromise<PartCrawlerPlatformSupplierVO[]> => {
  return request({
    url: '/kaisi/workbench/settings/platform-suppliers',
    method: 'get',
    params
  });
};

// 开启任务
export const startKaisiTask = (): AxiosPromise<string> => {
  return request({
    url: '/kaisi/workbench/task/start',
    method: 'post'
  });
};

// 停止任务
export const stopKaisiTask = () => {
  return request({
    url: '/kaisi/workbench/task/stop',
    method: 'post'
  });
};

// 执行一次
export const runOnceKaisiTask = (): AxiosPromise<string> => {
  return request({
    url: '/kaisi/workbench/task/run-once',
    method: 'post'
  });
};

// 查询时间线
export const listKaisiTimeline = (taskNo?: string, limit = 20): AxiosPromise<KaisiTimelineVO[]> => {
  return request({
    url: '/kaisi/workbench/timeline',
    method: 'get',
    params: { taskNo, limit }
  });
};

// 查询报价单列表
export const listKaisiQuotations = (query: KaisiQuotationQuery): AxiosPromise<KaisiQuotationVO[]> => {
  return request({
    url: '/kaisi/workbench/quotations',
    method: 'get',
    params: query
  });
};

// 查询报价单明细
export const listKaisiQuotationItems = (quotationId: string, storeId?: string): AxiosPromise<KaisiQuoteItemVO[]> => {
  return request({
    url: `/kaisi/workbench/quotations/${quotationId}/items`,
    method: 'get',
    params: { storeId }
  });
};

// 保存人工补价
export const saveKaisiManualPrice = (data: KaisiManualPriceForm) => {
  return request({
    url: '/kaisi/workbench/manual-price/save',
    method: 'post',
    data
  });
};

// 手动提交报价单
export const submitKaisiQuotation = (quotationId: string, storeId?: string) => {
  return request({
    url: `/kaisi/workbench/quotations/${quotationId}/submit`,
    method: 'post',
    params: { storeId }
  });
};

// 重试报价单
export const retryKaisiQuotation = (quotationId: string, storeId?: string) => {
  return request({
    url: `/kaisi/workbench/quotations/${quotationId}/retry`,
    method: 'post',
    params: { storeId }
  });
};

// 历史零件统计
export const listKaisiHistoryParts = (params: {
  beginTime?: string;
  endTime?: string;
  quotationId?: string;
  partsKeyword?: string;
}): AxiosPromise<KaisiHistoryPartVO[]> => {
  return request({
    url: '/kaisi/workbench/history/parts',
    method: 'get',
    params
  });
};

// 历史价格走势
export const listKaisiPriceTrend = (params: {
  beginTime?: string;
  endTime?: string;
  quotationId?: string;
  partsNum: string;
  brandName?: string;
  partsBrandQuality?: string;
}): AxiosPromise<KaisiPriceTrendPointVO[]> => {
  return request({
    url: '/kaisi/workbench/history/price-trend',
    method: 'get',
    params
  });
};
