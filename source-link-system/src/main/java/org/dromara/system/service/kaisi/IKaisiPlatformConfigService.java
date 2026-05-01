package org.dromara.system.service.kaisi;

import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.system.domain.bo.kaisi.*;
import org.dromara.system.domain.vo.kaisi.*;

import java.util.List;

/**
 * 平台配置管理服务
 */
public interface IKaisiPlatformConfigService {

    TableDataInfo<PartCrawlerPlatformVo> listPlatforms(PartCrawlerPlatformQueryBo bo, PageQuery pageQuery);

    List<PartCrawlerPlatformVo> listPlatformOptions();

    Long addPlatform(PartCrawlerPlatformSaveBo bo);

    void editPlatform(PartCrawlerPlatformSaveBo bo);

    void deletePlatform(Long id);

    TableDataInfo<PartCrawlerPlatformBrandVo> listPlatformBrands(PartCrawlerPlatformBrandQueryBo bo, PageQuery pageQuery);

    Long addPlatformBrand(PartCrawlerPlatformBrandSaveBo bo);

    void editPlatformBrand(PartCrawlerPlatformBrandSaveBo bo);

    void deletePlatformBrand(Long id);

    TableDataInfo<PartCrawlerPlatformQualityVo> listPlatformQualities(PartCrawlerPlatformQualityQueryBo bo, PageQuery pageQuery);

    Long addPlatformQuality(PartCrawlerPlatformQualitySaveBo bo);

    void editPlatformQuality(PartCrawlerPlatformQualitySaveBo bo);

    void deletePlatformQuality(Long id);

    TableDataInfo<PartCrawlerPlatformRegionVo> listPlatformRegions(PartCrawlerPlatformRegionQueryBo bo, PageQuery pageQuery);

    Long addPlatformRegion(PartCrawlerPlatformRegionSaveBo bo);

    void editPlatformRegion(PartCrawlerPlatformRegionSaveBo bo);

    void deletePlatformRegion(Long id);

    TableDataInfo<PartCrawlerPlatformSupplierVo> listPlatformSuppliers(PartCrawlerPlatformSupplierQueryBo bo, PageQuery pageQuery);

    Long addPlatformSupplier(PartCrawlerPlatformSupplierSaveBo bo);

    void editPlatformSupplier(PartCrawlerPlatformSupplierSaveBo bo);

    void deletePlatformSupplier(Long id);

    TableDataInfo<UserPartCrawlerPlatformConfigVo> listUserPlatformConfigs(UserPartCrawlerPlatformConfigQueryBo bo, PageQuery pageQuery);

    Long addUserPlatformConfig(UserPartCrawlerPlatformConfigSaveBo bo);

    void editUserPlatformConfig(UserPartCrawlerPlatformConfigSaveBo bo);

    void deleteUserPlatformConfig(Long id);
}

