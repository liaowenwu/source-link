package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 开思报价单列表视图
 */
@Data
public class KaisiQuotationVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String quotationId;

    private String inquiryId;

    private String storeId;

    private String statusIdDesc;

    private String flowStatus;

    private String processStatus;

    private String currentNodeCode;

    private String currentNodeName;

    private Integer itemCount;

    private Integer quotedItemCount;

    private Integer unquoteItemCount;

    private Integer submittedItemCount;

    private Integer exceptionItemCount;

    private Boolean manualPriceFillEnabled;

    private Boolean autoSubmitEnabled;

    private Boolean needAlert;

    private Long assignedUserId;

    private String lastMessage;

    private String errorMessage;

    private Date lastLogTime;
}

