package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 开思时间线视图
 */
@Data
public class KaisiTimelineVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String taskNo;

    private String eventType;

    private String eventLevel;

    private String displayTitle;

    private String displayContent;

    private String quotationId;

    private String storeId;

    private Date createTime;
}

