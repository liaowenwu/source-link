package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

/**
 * 开思价格走势点
 */
@Data
public class KaisiPriceTrendPointVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String quotationId;

    private String storeId;

    private String partsNum;

    private String partsName;

    private String brandName;

    private String partsBrandQuality;

    private BigDecimal suggestedPrice;

    private BigDecimal finalPrice;

    private Date quoteTime;
}

