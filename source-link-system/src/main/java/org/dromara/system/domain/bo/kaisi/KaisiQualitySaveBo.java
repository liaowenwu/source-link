package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 开思质量新增/修改参数
 */
@Data
public class KaisiQualitySaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 主键（修改时必填）
     */
    private Long id;

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
     * 质量类型
     */
    private Integer qualityType;

    /**
     * 排序号
     */
    private Integer orderNum;

    /**
     * 状态
     */
    private Integer status;
}

