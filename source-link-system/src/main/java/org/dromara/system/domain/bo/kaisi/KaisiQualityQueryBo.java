package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 开思质量查询参数
 */
@Data
public class KaisiQualityQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 质量编码（模糊）
     */
    private String qualityCode;

    /**
     * 质量名称（模糊）
     */
    private String qualityName;

    /**
     * 开思原始质量ID
     */
    private String qualityOriginId;

    /**
     * 状态
     */
    private Integer status;
}

