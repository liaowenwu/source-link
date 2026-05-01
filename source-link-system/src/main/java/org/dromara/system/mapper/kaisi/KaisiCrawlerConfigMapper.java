package org.dromara.system.mapper.kaisi;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Map;

/**
 * 开思抓价配置查询 Mapper
 */
@Mapper
public interface KaisiCrawlerConfigMapper {

    /**
     * 查询启用的平台
     */
    @Select({
        "SELECT id, platform_code AS platformCode, platform_name AS platformName",
        "FROM t_part_crawler_platform",
        "WHERE status = 1",
        "ORDER BY id ASC"
    })
    List<Map<String, Object>> selectActivePlatforms();

    /**
     * 查询用户开思工作台全局配置
     */
    @Select({
        "SELECT id, user_id AS userId, selected_platform_codes_json AS selectedPlatformCodesJson,",
        " crawl_strategy_type AS crawlStrategyType, auto_price_enabled AS autoPriceEnabled,",
        " auto_submit_enabled AS autoSubmitEnabled, quotation_crawl_concurrency AS quotationCrawlConcurrency,",
        " price_concurrency AS priceConcurrency, request_timeout_ms AS requestTimeoutMs,",
        " retry_times AS retryTimes, max_quotation_process_count AS maxQuotationProcessCount,",
        " manual_price_fill_enabled AS manualPriceFillEnabled",
        "FROM t_user_kaisi_config",
        "WHERE user_id = #{userId}",
        "ORDER BY update_time DESC",
        "LIMIT 1"
    })
    Map<String, Object> selectUserGlobalConfig(@Param("userId") Long userId);

    /**
     * 查询用户平台主配置（优先用户配置，不存在时取公共配置）
     */
    @Select({
        "<script>",
        "SELECT id, user_id AS userId, platform_id AS platformId, platform_code AS platformCode,",
        " default_city AS defaultCity, price_advantage_rate AS priceAdvantageRate,",
        " region_extra_days_json AS regionExtraDaysJson,",
        " single_sku_max_crawl_count AS singleSkuMaxCrawlCount,",
        " quality_origin_ids_json AS qualityOriginIdsJson,",
        " brand_origin_ids_json AS brandOriginIdsJson,",
        " region_origin_ids_json AS regionOriginIdsJson,",
        " supplier_configs_json AS supplierConfigsJson,",
        " default_markup_rate AS defaultMarkupRate,",
        " default_transfer_days AS defaultTransferDays,",
        " crawl_strategy_type AS crawlStrategyType,",
        " crawl_strategy_selected_platform_codes_json AS crawlStrategySelectedPlatformCodesJson,",
        " crawl_strategy_priority_platform_codes_json AS crawlStrategyPriorityPlatformCodesJson,",
        " crawl_strategy_stop_on_hit AS crawlStrategyStopOnHit",
        "FROM user_part_crawler_platform_config",
        "WHERE platform_code = #{platformCode}",
        "<if test='userId != null'>",
        "  AND (user_id = #{userId} OR user_id IS NULL)",
        "</if>",
        "ORDER BY CASE WHEN user_id = #{userId} THEN 0 ELSE 1 END, update_time DESC",
        "LIMIT 1",
        "</script>"
    })
    Map<String, Object> selectUserPlatformConfig(@Param("userId") Long userId, @Param("platformCode") String platformCode);

}
