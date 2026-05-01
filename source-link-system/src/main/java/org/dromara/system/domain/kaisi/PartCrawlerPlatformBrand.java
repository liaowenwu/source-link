package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 供应平台品牌
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("t_part_crawler_platform_brand")
public class PartCrawlerPlatformBrand extends TenantEntity {

    @TableId("id")
    private Long id;

    private Long platformId;

    private String brandName;

    private String brandOriginId;

    private Integer status;
}

