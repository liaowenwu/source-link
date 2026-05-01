package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 开思品牌配置
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("kaisi_brand")
public class KaisiBrand extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    /**
     * 品牌名称
     */
    private String brandName;

    /**
     * 开思原始品牌ID
     */
    private String brandOriginId;

    /**
     * 状态（1启用 0停用）
     */
    private Integer status;
}

