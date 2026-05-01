export interface KaisiBrandQuery {
  pageNum: number;
  pageSize: number;
  brandName?: string;
  brandOriginId?: string;
  status?: number;
}

export interface KaisiBrandVO {
  id: number;
  brandName: string;
  brandOriginId: string;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface KaisiBrandForm {
  id?: number;
  brandName: string;
  brandOriginId: string;
  status: number;
}

export interface KaisiQualityQuery {
  pageNum: number;
  pageSize: number;
  qualityCode?: string;
  qualityName?: string;
  qualityOriginId?: string;
  status?: number;
}

export interface KaisiQualityVO {
  id: number;
  qualityCode: string;
  qualityName: string;
  qualityOriginId: string;
  qualityType: number;
  orderNum: number;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface KaisiQualityForm {
  id?: number;
  qualityCode: string;
  qualityName: string;
  qualityOriginId: string;
  qualityType: number;
  orderNum: number;
  status: number;
}

export interface KaisiQualityBrandLinkQuery {
  pageNum: number;
  pageSize: number;
  kaisiQualityId?: number;
  kaisiBrandId?: number;
  status?: number;
  keyword?: string;
}

export interface KaisiQualityBrandLinkVO {
  id: number;
  kaisiQualityId: number;
  kaisiBrandId: number;
  qualityCode: string;
  qualityName: string;
  qualityOriginId: string;
  brandName: string;
  brandOriginId: string;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface KaisiQualityBrandLinkForm {
  id?: number;
  kaisiQualityId: number | undefined;
  kaisiBrandId: number | undefined;
  status: number;
}

export interface PartCrawlerPlatformQuery {
  pageNum: number;
  pageSize: number;
  platformCode?: string;
  platformName?: string;
  status?: number;
}

export interface PartCrawlerPlatformVO {
  id: number;
  platformCode: string;
  platformName: string;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface PartCrawlerPlatformForm {
  id?: number;
  platformCode: string;
  platformName: string;
  status: number;
}

export interface PartCrawlerPlatformBrandQuery {
  pageNum: number;
  pageSize: number;
  platformId?: number;
  brandName?: string;
  brandOriginId?: string;
  status?: number;
}

export interface PartCrawlerPlatformBrandVO {
  id: number;
  platformId: number;
  brandName: string;
  brandOriginId: string;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface PartCrawlerPlatformBrandForm {
  id?: number;
  platformId: number | undefined;
  brandName: string;
  brandOriginId: string;
  status: number;
}

export interface PartCrawlerPlatformQualityQuery {
  pageNum: number;
  pageSize: number;
  platformId?: number;
  qualityCode?: string;
  qualityName?: string;
  qualityOriginId?: string;
  status?: number;
}

export interface PartCrawlerPlatformQualityVO {
  id: number;
  platformId: number;
  qualityCode: string;
  qualityName: string;
  qualityOriginId: string;
  qualityType: number;
  orderNum: number;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface PartCrawlerPlatformQualityForm {
  id?: number;
  platformId: number | undefined;
  qualityCode: string;
  qualityName: string;
  qualityOriginId: string;
  qualityType: number;
  orderNum: number;
  status: number;
}

export interface PartCrawlerPlatformRegionQuery {
  pageNum: number;
  pageSize: number;
  platformId?: number;
  regionName?: string;
  regionOriginId?: string;
  status?: number;
}

export interface PartCrawlerPlatformRegionVO {
  id: number;
  platformId: number;
  regionName: string;
  regionOriginId: string;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface PartCrawlerPlatformRegionForm {
  id?: number;
  platformId: number | undefined;
  regionName: string;
  regionOriginId: string;
  status: number;
}

export interface PartCrawlerPlatformSupplierQuery {
  pageNum: number;
  pageSize: number;
  platformId?: number;
  supplierName?: string;
  supplierOriginId?: string;
  regionId?: number;
  status?: number;
}

export interface PartCrawlerPlatformSupplierVO {
  id: number;
  platformId: number;
  supplierName: string;
  supplierOriginId: string;
  regionId?: number;
  regionName?: string;
  status: number;
  createTime: string;
  updateTime: string;
}

export interface PartCrawlerPlatformSupplierForm {
  id?: number;
  platformId: number | undefined;
  supplierName: string;
  supplierOriginId: string;
  regionId?: number;
  regionName?: string;
  status: number;
}

export interface UserPartCrawlerPlatformConfigQuery {
  pageNum: number;
  pageSize: number;
  userId?: number;
  platformId?: number;
  platformCode?: string;
}

export interface UserPartCrawlerPlatformConfigVO {
  id: number;
  userId: number;
  platformId: number;
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
  createTime: string;
  updateTime: string;
}

export interface UserPartCrawlerPlatformConfigForm {
  id?: number;
  userId: number | undefined;
  platformId: number | undefined;
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
