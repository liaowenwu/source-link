package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

import java.math.BigDecimal;

/**
 * 用户平台抓价配置主表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("user_part_crawler_platform_config")
public class UserPartCrawlerPlatformConfig extends TenantEntity {

    @TableId("id")
    private Long id;

    private Long userId;

    private Long platformId;

    private String platformCode;

    private String defaultCity;

    private BigDecimal priceAdvantageRate;

    private String regionExtraDaysJson;

    private Integer singleSkuMaxCrawlCount;

    private String qualityOriginIdsJson;

    private String brandOriginIdsJson;

    private String regionOriginIdsJson;

    private String supplierConfigsJson;

    private BigDecimal defaultMarkupRate;

    private Integer defaultTransferDays;

    private String crawlStrategyType;

    private String crawlStrategySelectedPlatformCodesJson;

    private String crawlStrategyPriorityPlatformCodesJson;

    private Boolean crawlStrategyStopOnHit;
}

