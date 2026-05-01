package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

/**
 * 用户平台抓价配置返回对象
 */
@Data
public class UserPartCrawlerPlatformConfigVo implements Serializable {

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

    private Date createTime;

    private Date updateTime;
}

