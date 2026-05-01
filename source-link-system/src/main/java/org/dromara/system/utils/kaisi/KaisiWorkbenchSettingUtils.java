package org.dromara.system.utils.kaisi;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import org.dromara.system.domain.bo.kaisi.KaisiWorkbenchSettingSaveBo;
import org.dromara.system.domain.bo.kaisi.UserPartCrawlerPlatformConfigSaveBo;
import org.dromara.system.domain.kaisi.PartCrawlerPlatform;
import org.dromara.system.domain.kaisi.UserKaisiConfig;
import org.dromara.system.domain.kaisi.UserPartCrawlerPlatformConfig;
import org.dromara.system.domain.vo.kaisi.KaisiWorkbenchSettingVo;
import org.dromara.system.domain.vo.kaisi.UserPartCrawlerPlatformConfigVo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 开思工作台设置转换工具
 */
public class KaisiWorkbenchSettingUtils {

    private KaisiWorkbenchSettingUtils() {
    }

    public static KaisiWorkbenchSettingVo buildSettingVo(Long userId, UserKaisiConfig config, List<UserPartCrawlerPlatformConfig> platformRows) {
        KaisiWorkbenchSettingVo vo = buildDefaultSettingVo(userId);
        if (config != null) {
            vo.setId(config.getId());
            vo.setSelectedPlatformCodes(parseStringList(config.getSelectedPlatformCodesJson()));
            vo.setCrawlStrategyType(StrUtil.blankToDefault(config.getCrawlStrategyType(), "ALL"));
            vo.setAutoPriceEnabled(ObjectUtil.defaultIfNull(config.getAutoPriceEnabled(), Boolean.TRUE));
            vo.setAutoSubmitEnabled(ObjectUtil.defaultIfNull(config.getAutoSubmitEnabled(), Boolean.FALSE));
            vo.setQuotationCrawlConcurrency(defaultPositive(config.getQuotationCrawlConcurrency(), 1));
            vo.setPriceConcurrency(defaultPositive(config.getPriceConcurrency(), 1));
            vo.setRequestTimeoutMs(defaultPositive(config.getRequestTimeoutMs(), 30000));
            vo.setRetryTimes(ObjectUtil.defaultIfNull(config.getRetryTimes(), 3));
            vo.setMaxQuotationProcessCount(ObjectUtil.defaultIfNull(config.getMaxQuotationProcessCount(), 0));
            vo.setManualPriceFillEnabled(ObjectUtil.defaultIfNull(config.getManualPriceFillEnabled(), Boolean.FALSE));
        }
        vo.setPlatformConfigs(toPlatformConfigVoList(platformRows));
        return vo;
    }

    public static KaisiWorkbenchSettingVo buildDefaultSettingVo(Long userId) {
        KaisiWorkbenchSettingVo vo = new KaisiWorkbenchSettingVo();
        vo.setUserId(userId);
        vo.setSelectedPlatformCodes(Collections.emptyList());
        vo.setCrawlStrategyType("ALL");
        vo.setAutoPriceEnabled(Boolean.TRUE);
        vo.setAutoSubmitEnabled(Boolean.FALSE);
        vo.setQuotationCrawlConcurrency(1);
        vo.setPriceConcurrency(1);
        vo.setRequestTimeoutMs(30000);
        vo.setRetryTimes(3);
        vo.setMaxQuotationProcessCount(0);
        vo.setManualPriceFillEnabled(Boolean.FALSE);
        vo.setPlatformConfigs(Collections.emptyList());
        return vo;
    }

    public static UserKaisiConfig toUserKaisiConfig(Long userId, KaisiWorkbenchSettingSaveBo bo) {
        UserKaisiConfig row = new UserKaisiConfig();
        applyUserKaisiConfig(row, userId, bo);
        return row;
    }

    public static void applyUserKaisiConfig(UserKaisiConfig row, Long userId, KaisiWorkbenchSettingSaveBo bo) {
        row.setUserId(userId);
        row.setSelectedPlatformCodesJson(toJsonArrayText(bo.getSelectedPlatformCodes()));
        row.setCrawlStrategyType(StrUtil.blankToDefault(StrUtil.trim(bo.getCrawlStrategyType()), "ALL"));
        row.setAutoPriceEnabled(ObjectUtil.defaultIfNull(bo.getAutoPriceEnabled(), Boolean.TRUE));
        row.setAutoSubmitEnabled(ObjectUtil.defaultIfNull(bo.getAutoSubmitEnabled(), Boolean.FALSE));
        row.setQuotationCrawlConcurrency(defaultPositive(bo.getQuotationCrawlConcurrency(), 1));
        row.setPriceConcurrency(defaultPositive(bo.getPriceConcurrency(), 1));
        row.setRequestTimeoutMs(defaultPositive(bo.getRequestTimeoutMs(), 30000));
        row.setRetryTimes(Math.max(0, ObjectUtil.defaultIfNull(bo.getRetryTimes(), 3)));
        row.setMaxQuotationProcessCount(Math.max(0, ObjectUtil.defaultIfNull(bo.getMaxQuotationProcessCount(), 0)));
        row.setManualPriceFillEnabled(ObjectUtil.defaultIfNull(bo.getManualPriceFillEnabled(), Boolean.FALSE));
    }

    public static UserPartCrawlerPlatformConfig toUserPlatformConfig(Long userId, PartCrawlerPlatform platform, UserPartCrawlerPlatformConfigSaveBo bo) {
        UserPartCrawlerPlatformConfig row = new UserPartCrawlerPlatformConfig();
        applyUserPlatformConfig(row, userId, platform, bo);
        return row;
    }

    public static void applyUserPlatformConfig(UserPartCrawlerPlatformConfig row, Long userId, PartCrawlerPlatform platform, UserPartCrawlerPlatformConfigSaveBo bo) {
        row.setUserId(userId);
        row.setPlatformId(platform.getId());
        row.setPlatformCode(platform.getPlatformCode());
        row.setDefaultCity(StrUtil.trim(bo.getDefaultCity()));
        row.setPriceAdvantageRate(ObjectUtil.defaultIfNull(bo.getPriceAdvantageRate(), java.math.BigDecimal.valueOf(5)));
        row.setRegionExtraDaysJson(StrUtil.trim(bo.getRegionExtraDaysJson()));
        row.setSingleSkuMaxCrawlCount(ObjectUtil.defaultIfNull(bo.getSingleSkuMaxCrawlCount(), 0));
        row.setQualityOriginIdsJson(StrUtil.trim(bo.getQualityOriginIdsJson()));
        row.setBrandOriginIdsJson(StrUtil.trim(bo.getBrandOriginIdsJson()));
        row.setRegionOriginIdsJson(StrUtil.trim(bo.getRegionOriginIdsJson()));
        row.setSupplierConfigsJson(StrUtil.trim(bo.getSupplierConfigsJson()));
        row.setDefaultMarkupRate(ObjectUtil.defaultIfNull(bo.getDefaultMarkupRate(), java.math.BigDecimal.ZERO));
        row.setDefaultTransferDays(ObjectUtil.defaultIfNull(bo.getDefaultTransferDays(), 0));
        row.setCrawlStrategyType(StrUtil.blankToDefault(StrUtil.trim(bo.getCrawlStrategyType()), "FULL_SELECTED"));
        row.setCrawlStrategySelectedPlatformCodesJson(StrUtil.trim(bo.getCrawlStrategySelectedPlatformCodesJson()));
        row.setCrawlStrategyPriorityPlatformCodesJson(StrUtil.trim(bo.getCrawlStrategyPriorityPlatformCodesJson()));
        row.setCrawlStrategyStopOnHit(ObjectUtil.defaultIfNull(bo.getCrawlStrategyStopOnHit(), Boolean.FALSE));
    }

    public static List<String> parseStringList(String text) {
        if (StrUtil.isBlank(text) || !JSONUtil.isTypeJSONArray(text)) {
            return Collections.emptyList();
        }
        List<String> result = new ArrayList<>();
        for (Object item : JSONUtil.parseArray(text)) {
            String value = StrUtil.trim(String.valueOf(item));
            if (StrUtil.isNotBlank(value) && !result.contains(value)) {
                result.add(value);
            }
        }
        return result;
    }

    public static String toJsonArrayText(List<String> rows) {
        if (CollUtil.isEmpty(rows)) {
            return "[]";
        }
        List<String> result = new ArrayList<>();
        for (String item : rows) {
            String value = StrUtil.trim(item);
            if (StrUtil.isNotBlank(value) && !result.contains(value)) {
                result.add(value);
            }
        }
        return JSONUtil.toJsonStr(result);
    }

    /**
     * 将搜索框内容拆成多个关键词，支持空格、逗号、顿号和分号分隔
     */
    public static List<String> parseSearchKeywords(String text) {
        if (StrUtil.isBlank(text)) {
            return Collections.emptyList();
        }
        String normalized = text.replace('，', ',')
            .replace('、', ',')
            .replace('；', ',')
            .replace(';', ',')
            .replace(' ', ',');
        List<String> result = new ArrayList<>();
        for (String item : normalized.split(",")) {
            String value = StrUtil.trim(item);
            if (StrUtil.isNotBlank(value) && !result.contains(value)) {
                result.add(value);
            }
        }
        return result;
    }

    private static List<UserPartCrawlerPlatformConfigVo> toPlatformConfigVoList(List<UserPartCrawlerPlatformConfig> rows) {
        if (CollUtil.isEmpty(rows)) {
            return Collections.emptyList();
        }
        List<UserPartCrawlerPlatformConfigVo> result = new ArrayList<>(rows.size());
        for (UserPartCrawlerPlatformConfig row : rows) {
            result.add(KaisiPlatformConfigConvertUtils.toUserPlatformConfigVo(row));
        }
        return result;
    }

    private static Integer defaultPositive(Integer value, Integer defaultValue) {
        return Math.max(1, ObjectUtil.defaultIfNull(value, defaultValue));
    }
}
