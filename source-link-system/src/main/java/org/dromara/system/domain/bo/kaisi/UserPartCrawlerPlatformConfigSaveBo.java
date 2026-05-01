package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 用户平台抓价配置新增/修改参数
 */
@Data
public class UserPartCrawlerPlatformConfigSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

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

