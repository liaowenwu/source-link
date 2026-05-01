package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

import java.util.Date;

/**
 * 开思在线接单任务主表
 *
 * 说明：对应 Python 侧主任务 taskNo，承载首页服务状态与统计。
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("online_order_kaisi_task")
public class OnlineOrderKaisiTask extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    /**
     * 任务号（Python 侧 taskNo）
     */
    private String taskNo;

    /**
     * 任务类型（single/batch）
     */
    private String taskType;

    /**
     * 业务类型（KAISI_ONLINE_ORDER 等）
     */
    private String bizType;

    /**
     * 触发来源（frontend/online-order）
     */
    private String triggerBy;

    /**
     * 服务状态（INIT/STARTING/RUNNING/STOPPING/STOPPED/ERROR）
     */
    private String serviceStatus;

    /**
     * 任务总数（用于通用任务进度）
     */
    private Integer totalCount;

    /**
     * 成功数
     */
    private Integer successCount;

    /**
     * 失败数
     */
    private Integer failCount;

    /**
     * 今日抓取数
     */
    private Integer todayCatchCount;

    /**
     * 今日补价数
     */
    private Integer todayPriceCount;

    /**
     * 今日提交数
     */
    private Integer todaySubmitCount;

    /**
     * 当前节点编码
     */
    private String currentNodeCode;

    /**
     * 当前节点名称
     */
    private String currentNodeName;

    /**
     * 最新消息
     */
    private String currentMessage;

    /**
     * 错误消息
     */
    private String errorMessage;

    /**
     * 任务开始时间
     */
    private Date startedAt;

    /**
     * 任务停止时间
     */
    private Date stoppedAt;
}

