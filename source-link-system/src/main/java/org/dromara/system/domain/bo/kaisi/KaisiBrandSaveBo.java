package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 开思品牌新增/修改参数
 */
@Data
public class KaisiBrandSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 主键（修改时必填）
     */
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
     * 状态
     */
    private Integer status;
}

