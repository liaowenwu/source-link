package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台供应商新增/修改参数
 */
@Data
public class PartCrawlerPlatformSupplierSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long platformId;

    private String supplierName;

    private String supplierOriginId;

    private Long regionId;

    private String regionName;

    private Integer status;
}

