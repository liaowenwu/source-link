package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台品牌查询参数
 */
@Data
public class PartCrawlerPlatformBrandQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long platformId;

    private String brandName;

    private String brandOriginId;

    private Integer status;
}

