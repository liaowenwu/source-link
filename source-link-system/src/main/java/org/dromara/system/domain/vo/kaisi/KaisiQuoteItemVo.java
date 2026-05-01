package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 开思报价单明细视图
 */
@Data
public class KaisiQuoteItemVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private String quotationId;

    private String storeId;

    private String onlineOrderItemId;

    private String resolveResultId;

    private String partsNum;

    private String partsName;

    private String brandName;

    private String partsBrandQuality;

    private String storeServiceArea;

    private Integer quantity;

    private BigDecimal suggestedPrice;

    private BigDecimal finalPrice;

    private String itemProcessStatus;

    private String unmatchedReason;

    private String remark;
}

