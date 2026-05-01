package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台质量查询参数
 */
@Data
public class PartCrawlerPlatformQualityQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long platformId;

    private String qualityCode;

    private String qualityName;

    private String qualityOriginId;

    private Integer status;
}

