package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 开思质量与品牌关联配置
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("link_kaisi_quality_brand")
public class LinkKaisiQualityBrand extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    /**
     * 开思质量ID
     */
    private Long kaisiQualityId;

    /**
     * 开思品牌ID
     */
    private Long kaisiBrandId;

    /**
     * 质量编码
     */
    private String qualityCode;

    /**
     * 质量名称
     */
    private String qualityName;

    /**
     * 开思原始质量ID
     */
    private String qualityOriginId;

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

