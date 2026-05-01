package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 开思质量品牌关联新增/修改参数
 */
@Data
public class KaisiQualityBrandLinkSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 主键（修改时必填）
     */
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
     * 状态
     */
    private Integer status;
}

