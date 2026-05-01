package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台质量新增/修改参数
 */
@Data
public class PartCrawlerPlatformQualitySaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long platformId;

    private String qualityCode;

    private String qualityName;

    private String qualityOriginId;

    private Integer qualityType;

    private Integer orderNum;

    private Integer status;
}

