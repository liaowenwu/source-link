package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;

/**
 * 开思工作台设置保存参数
 */
@Data
public class KaisiWorkbenchSettingSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private List<String> selectedPlatformCodes;

    private String crawlStrategyType;

    private Boolean autoPriceEnabled;

    private Boolean autoSubmitEnabled;

    private Integer quotationCrawlConcurrency;

    private Integer priceConcurrency;

    private Integer requestTimeoutMs;

    private Integer retryTimes;

    private Integer maxQuotationProcessCount;

    private Boolean manualPriceFillEnabled;

    private List<UserPartCrawlerPlatformConfigSaveBo> platformConfigs;
}
