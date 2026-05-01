package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 用户开思工作台全局配置
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("t_user_kaisi_config")
public class UserKaisiConfig extends TenantEntity {

    @TableId("id")
    private Long id;

    private Long userId;

    private String selectedPlatformCodesJson;

    private String crawlStrategyType;

    private Boolean autoPriceEnabled;

    private Boolean autoSubmitEnabled;

    private Integer quotationCrawlConcurrency;

    private Integer priceConcurrency;

    private Integer requestTimeoutMs;

    private Integer retryTimes;

    private Integer maxQuotationProcessCount;

    private Boolean manualPriceFillEnabled;
}
