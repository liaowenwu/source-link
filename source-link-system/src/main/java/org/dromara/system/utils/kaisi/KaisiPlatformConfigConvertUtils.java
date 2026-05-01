package org.dromara.system.utils.kaisi;

import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.system.domain.bo.kaisi.*;
import org.dromara.system.domain.kaisi.*;
import org.dromara.system.domain.vo.kaisi.*;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 平台配置对象转换工具
 */
public class KaisiPlatformConfigConvertUtils {

    private KaisiPlatformConfigConvertUtils() {
    }

    public static Integer defaultStatus(Integer status) {
        return ObjectUtil.defaultIfNull(status, 1);
    }

    public static <T> TableDataInfo<T> buildTable(Page<?> source, List<T> records) {
        Page<T> voPage = new Page<>(source.getCurrent(), source.getSize(), source.getTotal());
        voPage.setRecords(records);
        return TableDataInfo.build(voPage);
    }

    public static boolean isIdConflict(Long selfId, Long targetId) {
        return targetId != null && (selfId == null || !targetId.equals(selfId));
    }

    public static PartCrawlerPlatform toPlatformEntity(PartCrawlerPlatformSaveBo bo) {
        PartCrawlerPlatform row = new PartCrawlerPlatform();
        applyPlatform(row, bo);
        return row;
    }

    public static void applyPlatform(PartCrawlerPlatform row, PartCrawlerPlatformSaveBo bo) {
        row.setPlatformCode(StrUtil.trim(bo.getPlatformCode()));
        row.setPlatformName(StrUtil.trim(bo.getPlatformName()));
        row.setStatus(defaultStatus(bo.getStatus()));
    }

    public static PartCrawlerPlatformVo toPlatformVo(PartCrawlerPlatform row) {
        PartCrawlerPlatformVo vo = new PartCrawlerPlatformVo();
        vo.setId(row.getId());
        vo.setPlatformCode(row.getPlatformCode());
        vo.setPlatformName(row.getPlatformName());
        vo.setStatus(row.getStatus());
        vo.setCreateTime(row.getCreateTime());
        vo.setUpdateTime(row.getUpdateTime());
        return vo;
    }

    public static List<PartCrawlerPlatformVo> toPlatformVoList(List<PartCrawlerPlatform> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<PartCrawlerPlatformVo> result = new ArrayList<>(rows.size());
        for (PartCrawlerPlatform row : rows) {
            result.add(toPlatformVo(row));
        }
        return result;
    }

    public static PartCrawlerPlatformBrand toPlatformBrandEntity(PartCrawlerPlatformBrandSaveBo bo) {
        PartCrawlerPlatformBrand row = new PartCrawlerPlatformBrand();
        applyPlatformBrand(row, bo);
        return row;
    }

    public static void applyPlatformBrand(PartCrawlerPlatformBrand row, PartCrawlerPlatformBrandSaveBo bo) {
        row.setPlatformId(bo.getPlatformId());
        row.setBrandName(StrUtil.trim(bo.getBrandName()));
        row.setBrandOriginId(StrUtil.trim(bo.getBrandOriginId()));
        row.setStatus(defaultStatus(bo.getStatus()));
    }

    public static PartCrawlerPlatformBrandVo toPlatformBrandVo(PartCrawlerPlatformBrand row) {
        PartCrawlerPlatformBrandVo vo = new PartCrawlerPlatformBrandVo();
        vo.setId(row.getId());
        vo.setPlatformId(row.getPlatformId());
        vo.setBrandName(row.getBrandName());
        vo.setBrandOriginId(row.getBrandOriginId());
        vo.setStatus(row.getStatus());
        vo.setCreateTime(row.getCreateTime());
        vo.setUpdateTime(row.getUpdateTime());
        return vo;
    }

    public static List<PartCrawlerPlatformBrandVo> toPlatformBrandVoList(List<PartCrawlerPlatformBrand> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<PartCrawlerPlatformBrandVo> result = new ArrayList<>(rows.size());
        for (PartCrawlerPlatformBrand row : rows) {
            result.add(toPlatformBrandVo(row));
        }
        return result;
    }

    public static PartCrawlerPlatformQuality toPlatformQualityEntity(PartCrawlerPlatformQualitySaveBo bo) {
        PartCrawlerPlatformQuality row = new PartCrawlerPlatformQuality();
        applyPlatformQuality(row, bo);
        return row;
    }

    public static void applyPlatformQuality(PartCrawlerPlatformQuality row, PartCrawlerPlatformQualitySaveBo bo) {
        row.setPlatformId(bo.getPlatformId());
        row.setQualityCode(StrUtil.trim(bo.getQualityCode()));
        row.setQualityName(StrUtil.trim(bo.getQualityName()));
        row.setQualityOriginId(StrUtil.trim(bo.getQualityOriginId()));
        row.setQualityType(ObjectUtil.defaultIfNull(bo.getQualityType(), 0));
        row.setOrderNum(ObjectUtil.defaultIfNull(bo.getOrderNum(), 0));
        row.setStatus(defaultStatus(bo.getStatus()));
    }

    public static PartCrawlerPlatformQualityVo toPlatformQualityVo(PartCrawlerPlatformQuality row) {
        PartCrawlerPlatformQualityVo vo = new PartCrawlerPlatformQualityVo();
        vo.setId(row.getId());
        vo.setPlatformId(row.getPlatformId());
        vo.setQualityCode(row.getQualityCode());
        vo.setQualityName(row.getQualityName());
        vo.setQualityOriginId(row.getQualityOriginId());
        vo.setQualityType(row.getQualityType());
        vo.setOrderNum(row.getOrderNum());
        vo.setStatus(row.getStatus());
        vo.setCreateTime(row.getCreateTime());
        vo.setUpdateTime(row.getUpdateTime());
        return vo;
    }

    public static List<PartCrawlerPlatformQualityVo> toPlatformQualityVoList(List<PartCrawlerPlatformQuality> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<PartCrawlerPlatformQualityVo> result = new ArrayList<>(rows.size());
        for (PartCrawlerPlatformQuality row : rows) {
            result.add(toPlatformQualityVo(row));
        }
        return result;
    }

    public static PartCrawlerPlatformRegion toPlatformRegionEntity(PartCrawlerPlatformRegionSaveBo bo) {
        PartCrawlerPlatformRegion row = new PartCrawlerPlatformRegion();
        applyPlatformRegion(row, bo);
        return row;
    }

    public static void applyPlatformRegion(PartCrawlerPlatformRegion row, PartCrawlerPlatformRegionSaveBo bo) {
        row.setPlatformId(bo.getPlatformId());
        row.setRegionName(StrUtil.trim(bo.getRegionName()));
        row.setRegionOriginId(StrUtil.trim(bo.getRegionOriginId()));
        row.setStatus(defaultStatus(bo.getStatus()));
    }

    public static PartCrawlerPlatformRegionVo toPlatformRegionVo(PartCrawlerPlatformRegion row) {
        PartCrawlerPlatformRegionVo vo = new PartCrawlerPlatformRegionVo();
        vo.setId(row.getId());
        vo.setPlatformId(row.getPlatformId());
        vo.setRegionName(row.getRegionName());
        vo.setRegionOriginId(row.getRegionOriginId());
        vo.setStatus(row.getStatus());
        vo.setCreateTime(row.getCreateTime());
        vo.setUpdateTime(row.getUpdateTime());
        return vo;
    }

    public static List<PartCrawlerPlatformRegionVo> toPlatformRegionVoList(List<PartCrawlerPlatformRegion> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<PartCrawlerPlatformRegionVo> result = new ArrayList<>(rows.size());
        for (PartCrawlerPlatformRegion row : rows) {
            result.add(toPlatformRegionVo(row));
        }
        return result;
    }

    public static PartCrawlerPlatformSupplier toPlatformSupplierEntity(PartCrawlerPlatformSupplierSaveBo bo) {
        PartCrawlerPlatformSupplier row = new PartCrawlerPlatformSupplier();
        applyPlatformSupplier(row, bo);
        return row;
    }

    public static void applyPlatformSupplier(PartCrawlerPlatformSupplier row, PartCrawlerPlatformSupplierSaveBo bo) {
        row.setPlatformId(bo.getPlatformId());
        row.setSupplierName(StrUtil.trim(bo.getSupplierName()));
        row.setSupplierOriginId(StrUtil.trim(bo.getSupplierOriginId()));
        row.setRegionId(bo.getRegionId());
        row.setRegionName(StrUtil.trim(bo.getRegionName()));
        row.setStatus(defaultStatus(bo.getStatus()));
    }

    public static PartCrawlerPlatformSupplierVo toPlatformSupplierVo(PartCrawlerPlatformSupplier row) {
        PartCrawlerPlatformSupplierVo vo = new PartCrawlerPlatformSupplierVo();
        vo.setId(row.getId());
        vo.setPlatformId(row.getPlatformId());
        vo.setSupplierName(row.getSupplierName());
        vo.setSupplierOriginId(row.getSupplierOriginId());
        vo.setRegionId(row.getRegionId());
        vo.setRegionName(row.getRegionName());
        vo.setStatus(row.getStatus());
        vo.setCreateTime(row.getCreateTime());
        vo.setUpdateTime(row.getUpdateTime());
        return vo;
    }

    public static List<PartCrawlerPlatformSupplierVo> toPlatformSupplierVoList(List<PartCrawlerPlatformSupplier> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<PartCrawlerPlatformSupplierVo> result = new ArrayList<>(rows.size());
        for (PartCrawlerPlatformSupplier row : rows) {
            result.add(toPlatformSupplierVo(row));
        }
        return result;
    }

    public static UserPartCrawlerPlatformConfig toUserPlatformConfigEntity(UserPartCrawlerPlatformConfigSaveBo bo) {
        UserPartCrawlerPlatformConfig row = new UserPartCrawlerPlatformConfig();
        applyUserPlatformConfig(row, bo);
        return row;
    }

    public static void applyUserPlatformConfig(UserPartCrawlerPlatformConfig row, UserPartCrawlerPlatformConfigSaveBo bo) {
        row.setUserId(bo.getUserId());
        row.setPlatformId(bo.getPlatformId());
        row.setPlatformCode(StrUtil.trim(bo.getPlatformCode()));
        row.setDefaultCity(StrUtil.trim(bo.getDefaultCity()));
        row.setPriceAdvantageRate(ObjectUtil.defaultIfNull(bo.getPriceAdvantageRate(), BigDecimal.valueOf(5)));
        row.setRegionExtraDaysJson(StrUtil.trim(bo.getRegionExtraDaysJson()));
        row.setSingleSkuMaxCrawlCount(ObjectUtil.defaultIfNull(bo.getSingleSkuMaxCrawlCount(), 0));
        row.setQualityOriginIdsJson(StrUtil.trim(bo.getQualityOriginIdsJson()));
        row.setBrandOriginIdsJson(StrUtil.trim(bo.getBrandOriginIdsJson()));
        row.setRegionOriginIdsJson(StrUtil.trim(bo.getRegionOriginIdsJson()));
        row.setSupplierConfigsJson(StrUtil.trim(bo.getSupplierConfigsJson()));
        row.setDefaultMarkupRate(ObjectUtil.defaultIfNull(bo.getDefaultMarkupRate(), BigDecimal.ZERO));
        row.setDefaultTransferDays(ObjectUtil.defaultIfNull(bo.getDefaultTransferDays(), 0));
        row.setCrawlStrategyType(StrUtil.blankToDefault(StrUtil.trim(bo.getCrawlStrategyType()), "FULL_SELECTED"));
        row.setCrawlStrategySelectedPlatformCodesJson(StrUtil.trim(bo.getCrawlStrategySelectedPlatformCodesJson()));
        row.setCrawlStrategyPriorityPlatformCodesJson(StrUtil.trim(bo.getCrawlStrategyPriorityPlatformCodesJson()));
        row.setCrawlStrategyStopOnHit(ObjectUtil.defaultIfNull(bo.getCrawlStrategyStopOnHit(), Boolean.FALSE));
    }

    public static UserPartCrawlerPlatformConfigVo toUserPlatformConfigVo(UserPartCrawlerPlatformConfig row) {
        UserPartCrawlerPlatformConfigVo vo = new UserPartCrawlerPlatformConfigVo();
        vo.setId(row.getId());
        vo.setUserId(row.getUserId());
        vo.setPlatformId(row.getPlatformId());
        vo.setPlatformCode(row.getPlatformCode());
        vo.setDefaultCity(row.getDefaultCity());
        vo.setPriceAdvantageRate(row.getPriceAdvantageRate());
        vo.setRegionExtraDaysJson(row.getRegionExtraDaysJson());
        vo.setSingleSkuMaxCrawlCount(row.getSingleSkuMaxCrawlCount());
        vo.setQualityOriginIdsJson(row.getQualityOriginIdsJson());
        vo.setBrandOriginIdsJson(row.getBrandOriginIdsJson());
        vo.setRegionOriginIdsJson(row.getRegionOriginIdsJson());
        vo.setSupplierConfigsJson(row.getSupplierConfigsJson());
        vo.setDefaultMarkupRate(row.getDefaultMarkupRate());
        vo.setDefaultTransferDays(row.getDefaultTransferDays());
        vo.setCrawlStrategyType(row.getCrawlStrategyType());
        vo.setCrawlStrategySelectedPlatformCodesJson(row.getCrawlStrategySelectedPlatformCodesJson());
        vo.setCrawlStrategyPriorityPlatformCodesJson(row.getCrawlStrategyPriorityPlatformCodesJson());
        vo.setCrawlStrategyStopOnHit(row.getCrawlStrategyStopOnHit());
        vo.setCreateTime(row.getCreateTime());
        vo.setUpdateTime(row.getUpdateTime());
        return vo;
    }

    public static List<UserPartCrawlerPlatformConfigVo> toUserPlatformConfigVoList(List<UserPartCrawlerPlatformConfig> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<UserPartCrawlerPlatformConfigVo> result = new ArrayList<>(rows.size());
        for (UserPartCrawlerPlatformConfig row : rows) {
            result.add(toUserPlatformConfigVo(row));
        }
        return result;
    }
}

