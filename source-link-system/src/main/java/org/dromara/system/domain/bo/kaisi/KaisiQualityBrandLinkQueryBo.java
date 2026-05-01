package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 开思质量品牌关联查询参数
 */
@Data
public class KaisiQualityBrandLinkQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 质量ID
     */
    private Long kaisiQualityId;

    /**
     * 品牌ID
     */
    private Long kaisiBrandId;

    /**
     * 状态
     */
    private Integer status;

    /**
     * 关键字（质量/品牌名称）
     */
    private String keyword;
}

