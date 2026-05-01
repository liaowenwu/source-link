package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 人工补价保存参数
 */
@Data
public class KaisiManualPriceSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long itemId;

    private String quotationId;

    private String storeId;

    private BigDecimal finalPrice;

    private String unmatchedReason;

    private String remark;
}

