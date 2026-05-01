import request from '@/utils/request';
import { AxiosPromise } from 'axios';
import {
  KaisiBrandForm,
  KaisiBrandQuery,
  KaisiBrandVO,
  KaisiQualityBrandLinkForm,
  KaisiQualityBrandLinkQuery,
  KaisiQualityBrandLinkVO,
  KaisiQualityForm,
  KaisiQualityQuery,
  KaisiQualityVO,
  PartCrawlerPlatformBrandForm,
  PartCrawlerPlatformBrandQuery,
  PartCrawlerPlatformBrandVO,
  PartCrawlerPlatformForm,
  PartCrawlerPlatformQuery,
  PartCrawlerPlatformQualityForm,
  PartCrawlerPlatformQualityQuery,
  PartCrawlerPlatformQualityVO,
  PartCrawlerPlatformRegionForm,
  PartCrawlerPlatformRegionQuery,
  PartCrawlerPlatformRegionVO,
  PartCrawlerPlatformSupplierForm,
  PartCrawlerPlatformSupplierQuery,
  PartCrawlerPlatformSupplierVO,
  PartCrawlerPlatformVO,
  UserPartCrawlerPlatformConfigForm,
  UserPartCrawlerPlatformConfigQuery,
  UserPartCrawlerPlatformConfigVO
} from './types';

// 查询品牌列表
export const listKaisiBrands = (query: KaisiBrandQuery): AxiosPromise<KaisiBrandVO[]> => {
  return request({
    url: '/kaisi/base-config/brands',
    method: 'get',
    params: query
  });
};

// 查询品牌下拉
export const listKaisiBrandOptions = (): AxiosPromise<KaisiBrandVO[]> => {
  return request({
    url: '/kaisi/base-config/brands/options',
    method: 'get'
  });
};

// 新增品牌
export const addKaisiBrand = (data: KaisiBrandForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/brands',
    method: 'post',
    data
  });
};

// 修改品牌
export const updateKaisiBrand = (data: KaisiBrandForm) => {
  return request({
    url: '/kaisi/base-config/brands',
    method: 'put',
    data
  });
};

// 删除品牌
export const deleteKaisiBrand = (id: number) => {
  return request({
    url: `/kaisi/base-config/brands/${id}`,
    method: 'delete'
  });
};

// 查询质量列表
export const listKaisiQualities = (query: KaisiQualityQuery): AxiosPromise<KaisiQualityVO[]> => {
  return request({
    url: '/kaisi/base-config/qualities',
    method: 'get',
    params: query
  });
};

// 查询质量下拉
export const listKaisiQualityOptions = (): AxiosPromise<KaisiQualityVO[]> => {
  return request({
    url: '/kaisi/base-config/qualities/options',
    method: 'get'
  });
};

// 新增质量
export const addKaisiQuality = (data: KaisiQualityForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/qualities',
    method: 'post',
    data
  });
};

// 修改质量
export const updateKaisiQuality = (data: KaisiQualityForm) => {
  return request({
    url: '/kaisi/base-config/qualities',
    method: 'put',
    data
  });
};

// 删除质量
export const deleteKaisiQuality = (id: number) => {
  return request({
    url: `/kaisi/base-config/qualities/${id}`,
    method: 'delete'
  });
};

// 查询质量品牌关联列表
export const listKaisiQualityBrandLinks = (query: KaisiQualityBrandLinkQuery): AxiosPromise<KaisiQualityBrandLinkVO[]> => {
  return request({
    url: '/kaisi/base-config/quality-brand-links',
    method: 'get',
    params: query
  });
};

// 新增质量品牌关联
export const addKaisiQualityBrandLink = (data: KaisiQualityBrandLinkForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/quality-brand-links',
    method: 'post',
    data
  });
};

// 修改质量品牌关联
export const updateKaisiQualityBrandLink = (data: KaisiQualityBrandLinkForm) => {
  return request({
    url: '/kaisi/base-config/quality-brand-links',
    method: 'put',
    data
  });
};

// 删除质量品牌关联
export const deleteKaisiQualityBrandLink = (id: number) => {
  return request({
    url: `/kaisi/base-config/quality-brand-links/${id}`,
    method: 'delete'
  });
};

// 查询平台列表
export const listPartCrawlerPlatforms = (query: PartCrawlerPlatformQuery): AxiosPromise<PartCrawlerPlatformVO[]> => {
  return request({
    url: '/kaisi/base-config/platforms',
    method: 'get',
    params: query
  });
};

// 查询平台下拉
export const listPartCrawlerPlatformOptions = (): AxiosPromise<PartCrawlerPlatformVO[]> => {
  return request({
    url: '/kaisi/base-config/platforms/options',
    method: 'get'
  });
};

// 新增平台
export const addPartCrawlerPlatform = (data: PartCrawlerPlatformForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/platforms',
    method: 'post',
    data
  });
};

// 修改平台
export const updatePartCrawlerPlatform = (data: PartCrawlerPlatformForm) => {
  return request({
    url: '/kaisi/base-config/platforms',
    method: 'put',
    data
  });
};

// 删除平台
export const deletePartCrawlerPlatform = (id: number) => {
  return request({
    url: `/kaisi/base-config/platforms/${id}`,
    method: 'delete'
  });
};

// 查询平台品牌列表
export const listPartCrawlerPlatformBrands = (query: PartCrawlerPlatformBrandQuery): AxiosPromise<PartCrawlerPlatformBrandVO[]> => {
  return request({
    url: '/kaisi/base-config/platform-brands',
    method: 'get',
    params: query
  });
};

export const addPartCrawlerPlatformBrand = (data: PartCrawlerPlatformBrandForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/platform-brands',
    method: 'post',
    data
  });
};

export const updatePartCrawlerPlatformBrand = (data: PartCrawlerPlatformBrandForm) => {
  return request({
    url: '/kaisi/base-config/platform-brands',
    method: 'put',
    data
  });
};

export const deletePartCrawlerPlatformBrand = (id: number) => {
  return request({
    url: `/kaisi/base-config/platform-brands/${id}`,
    method: 'delete'
  });
};

// 查询平台质量列表
export const listPartCrawlerPlatformQualities = (query: PartCrawlerPlatformQualityQuery): AxiosPromise<PartCrawlerPlatformQualityVO[]> => {
  return request({
    url: '/kaisi/base-config/platform-qualities',
    method: 'get',
    params: query
  });
};

export const addPartCrawlerPlatformQuality = (data: PartCrawlerPlatformQualityForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/platform-qualities',
    method: 'post',
    data
  });
};

export const updatePartCrawlerPlatformQuality = (data: PartCrawlerPlatformQualityForm) => {
  return request({
    url: '/kaisi/base-config/platform-qualities',
    method: 'put',
    data
  });
};

export const deletePartCrawlerPlatformQuality = (id: number) => {
  return request({
    url: `/kaisi/base-config/platform-qualities/${id}`,
    method: 'delete'
  });
};

// 查询平台区域列表
export const listPartCrawlerPlatformRegions = (query: PartCrawlerPlatformRegionQuery): AxiosPromise<PartCrawlerPlatformRegionVO[]> => {
  return request({
    url: '/kaisi/base-config/platform-regions',
    method: 'get',
    params: query
  });
};

export const addPartCrawlerPlatformRegion = (data: PartCrawlerPlatformRegionForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/platform-regions',
    method: 'post',
    data
  });
};

export const updatePartCrawlerPlatformRegion = (data: PartCrawlerPlatformRegionForm) => {
  return request({
    url: '/kaisi/base-config/platform-regions',
    method: 'put',
    data
  });
};

export const deletePartCrawlerPlatformRegion = (id: number) => {
  return request({
    url: `/kaisi/base-config/platform-regions/${id}`,
    method: 'delete'
  });
};

// 查询平台供应商列表
export const listPartCrawlerPlatformSuppliers = (query: PartCrawlerPlatformSupplierQuery): AxiosPromise<PartCrawlerPlatformSupplierVO[]> => {
  return request({
    url: '/kaisi/base-config/platform-suppliers',
    method: 'get',
    params: query
  });
};

export const addPartCrawlerPlatformSupplier = (data: PartCrawlerPlatformSupplierForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/platform-suppliers',
    method: 'post',
    data
  });
};

export const updatePartCrawlerPlatformSupplier = (data: PartCrawlerPlatformSupplierForm) => {
  return request({
    url: '/kaisi/base-config/platform-suppliers',
    method: 'put',
    data
  });
};

export const deletePartCrawlerPlatformSupplier = (id: number) => {
  return request({
    url: `/kaisi/base-config/platform-suppliers/${id}`,
    method: 'delete'
  });
};

// 查询用户平台抓价配置列表
export const listUserPartCrawlerPlatformConfigs = (query: UserPartCrawlerPlatformConfigQuery): AxiosPromise<UserPartCrawlerPlatformConfigVO[]> => {
  return request({
    url: '/kaisi/base-config/user-platform-configs',
    method: 'get',
    params: query
  });
};

export const addUserPartCrawlerPlatformConfig = (data: UserPartCrawlerPlatformConfigForm): AxiosPromise<number> => {
  return request({
    url: '/kaisi/base-config/user-platform-configs',
    method: 'post',
    data
  });
};

export const updateUserPartCrawlerPlatformConfig = (data: UserPartCrawlerPlatformConfigForm) => {
  return request({
    url: '/kaisi/base-config/user-platform-configs',
    method: 'put',
    data
  });
};

export const deleteUserPartCrawlerPlatformConfig = (id: number) => {
  return request({
    url: `/kaisi/base-config/user-platform-configs/${id}`,
    method: 'delete'
  });
};
