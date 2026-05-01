package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 供应平台质量
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("t_part_crawler_platform_quality")
public class PartCrawlerPlatformQuality extends TenantEntity {

    @TableId("id")
    private Long id;

    private Long platformId;

    private String qualityCode;

    private String qualityName;

    private String qualityOriginId;

    private Integer qualityType;

    private Integer orderNum;

    private Integer status;
}

