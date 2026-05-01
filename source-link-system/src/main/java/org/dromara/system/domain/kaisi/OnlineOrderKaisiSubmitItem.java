package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

import java.util.Date;

/**
 * 开思提交结果明细表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("online_order_kaisi_submit_item")
public class OnlineOrderKaisiSubmitItem extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    private String taskNo;

    private String quotationId;

    private String storeId;

    private String resolveResultId;

    private String partsNum;

    private String partsName;

    private String submitStatus;

    private String submitRequest;

    private String submitResponse;

    private String errorMessage;

    private Date submittedAt;
}

