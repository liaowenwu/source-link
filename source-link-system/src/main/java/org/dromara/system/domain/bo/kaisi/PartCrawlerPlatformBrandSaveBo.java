package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台品牌新增/修改参数
 */
@Data
public class PartCrawlerPlatformBrandSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long platformId;

    private String brandName;

    private String brandOriginId;

    private Integer status;
}

