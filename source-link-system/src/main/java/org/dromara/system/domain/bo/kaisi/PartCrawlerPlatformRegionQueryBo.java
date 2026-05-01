package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台区域查询参数
 */
@Data
public class PartCrawlerPlatformRegionQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long platformId;

    private String regionName;

    private String regionOriginId;

    private Integer status;
}

