package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 开思品牌查询参数
 */
@Data
public class KaisiBrandQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 品牌名称（模糊）
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

