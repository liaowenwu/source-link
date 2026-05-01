package org.dromara.system.domain.bo.kaisi;

import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.mybatis.core.domain.BaseEntity;

/**
 * 开思报价单查询参数
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class KaisiQuotationQueryBo extends BaseEntity {

    private String quotationId;

    private String inquiryId;

    private String storeId;

    private String flowStatus;

    private String processStatus;

    /**
     * 查询场景：TODAY/MANUAL/HISTORY
     */
    private String scene;

    /**
     * 是否手动补价
     */
    private Boolean manualPriceFillEnabled;

    /**
     * 开始时间（yyyy-MM-dd HH:mm:ss）
     */
    private String beginTime;

    /**
     * 结束时间（yyyy-MM-dd HH:mm:ss）
     */
    private String endTime;

    private Boolean needAlert;

    private Long assignedUserId;
}
