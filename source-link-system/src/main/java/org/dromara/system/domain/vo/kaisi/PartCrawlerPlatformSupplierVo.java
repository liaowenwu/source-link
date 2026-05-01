package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 平台供应商返回对象
 */
@Data
public class PartCrawlerPlatformSupplierVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long platformId;

    private String supplierName;

    private String supplierOriginId;

    private Long regionId;

    private String regionName;

    private Integer status;

    private Date createTime;

    private Date updateTime;
}

