package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台主表查询参数
 */
@Data
public class PartCrawlerPlatformQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String platformCode;

    private String platformName;

    private Integer status;
}

