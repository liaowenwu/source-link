package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

import java.util.Date;

/**
 * 开思报价单主表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("online_order_kaisi_quotation")
public class OnlineOrderKaisiQuotation extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    /**
     * 报价单号
     */
    private String quotationId;

    /**
     * 询价单号
     */
    private String inquiryId;

    /**
     * 门店号
     */
    private String storeId;

    /**
     * 供应商公司 ID
     */
    private String supplierCompanyId;

    /**
     * 外部状态编码
     */
    private String statusId;

    /**
     * 外部状态描述
     */
    private String statusIdDesc;

    /**
     * 流程状态（WAIT_PRICE_FILL/WAIT_SUBMIT/COMPLETED...）
     */
    private String flowStatus;

    /**
     * 处理状态（PROCESSING/SUCCESS/FAILED）
     */
    private String processStatus;

    /**
     * 当前节点编码
     */
    private String currentNodeCode;

    /**
     * 当前节点名称
     */
    private String currentNodeName;

    /**
     * 是否手动补价
     */
    private Boolean manualPriceFillEnabled;

    /**
     * 是否自动提交
     */
    private Boolean autoSubmitEnabled;

    /**
     * 明细总数
     */
    private Integer itemCount;

    /**
     * 已补价明细数
     */
    private Integer quotedItemCount;

    /**
     * 未补价明细数
     */
    private Integer unquoteItemCount;

    /**
     * 已提交明细数
     */
    private Integer submittedItemCount;

    /**
     * 异常明细数
     */
    private Integer exceptionItemCount;

    /**
     * 是否需要人工处理
     */
    private Boolean needManualHandle;

    /**
     * 是否首页告警
     */
    private Boolean needAlert;

    /**
     * 分配处理人
     */
    private Long assignedUserId;

    /**
     * 最新消息
     */
    private String lastMessage;

    /**
     * 错误消息
     */
    private String errorMessage;

    /**
     * 原始报文
     */
    private String rawPayload;

    /**
     * 最近更新时间
     */
    private Date lastLogTime;
}

