package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 供应平台供应商
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("t_part_crawler_platform_supplier")
public class PartCrawlerPlatformSupplier extends TenantEntity {

    @TableId("id")
    private Long id;

    private Long platformId;

    private String supplierName;

    private String supplierOriginId;

    private Long regionId;

    private String regionName;

    private Integer status;
}

