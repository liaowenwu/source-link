package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 开思任务日志表
 *
 * 说明：服务级时间线日志。
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("online_order_kaisi_task_log")
public class OnlineOrderKaisiTaskLog extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    /**
     * 任务号
     */
    private String taskNo;

    /**
     * 事件编码
     */
    private String eventCode;

    /**
     * 事件类型
     */
    private String eventType;

    /**
     * 事件等级
     */
    private String eventLevel;

    /**
     * 时间线标题
     */
    private String displayTitle;

    /**
     * 时间线内容
     */
    private String displayContent;

    /**
     * 关联报价单号
     */
    private String quotationId;

    /**
     * 关联门店号
     */
    private String storeId;

    /**
     * 原始载荷（JSON 字符串）
     */
    private String rawPayload;
}

