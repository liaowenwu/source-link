package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

/**
 * 开思历史零件统计视图
 */
@Data
public class KaisiHistoryPartVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String partsNum;

    private String partsName;

    private String brandName;

    private String partsBrandQuality;

    /**
     * 报价次数
     */
    private Integer quoteTimes;

    /**
     * 平均报价
     */
    private BigDecimal avgFinalPrice;

    /**
     * 最近报价时间
     */
    private Date latestQuoteTime;
}

