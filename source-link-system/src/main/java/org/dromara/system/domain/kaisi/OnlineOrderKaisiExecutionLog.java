package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 开思报价单执行日志
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("online_order_kaisi_execution_log")
public class OnlineOrderKaisiExecutionLog extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    private String taskNo;

    private String quotationId;

    private String storeId;

    private String flowStatus;

    private String processStatus;

    private String currentNodeCode;

    private String currentNodeName;

    private String eventType;

    private String logLevel;

    private String message;

    private String rawPayload;
}

