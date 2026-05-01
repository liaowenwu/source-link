package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 供应平台主表
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("t_part_crawler_platform")
public class PartCrawlerPlatform extends TenantEntity {

    @TableId("id")
    private Long id;

    private String platformCode;

    private String platformName;

    private Integer status;
}

