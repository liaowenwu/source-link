package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 同步任务创建参数
 */
@Data
public class KaisiSyncTaskCreateBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String taskType;

    private String bizType;

    private String triggerBy;

    private Integer totalCount;

    private String sku;

    private List<String> skus;

    private Map<String, Object> taskParams;
}

