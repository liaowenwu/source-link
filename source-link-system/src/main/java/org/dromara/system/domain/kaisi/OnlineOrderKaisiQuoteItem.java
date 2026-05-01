package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

import java.math.BigDecimal;

/**
 * 开思报价单明细表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("online_order_kaisi_quote_item")
public class OnlineOrderKaisiQuoteItem extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    private String quotationId;

    private String storeId;

    /**
     * 在线明细 ID（Python 同步字段）
     */
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

    private String rawPayload;
}

