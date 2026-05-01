package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 开思质量品牌关联返回对象
 */
@Data
public class KaisiQualityBrandLinkVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long kaisiQualityId;

    private Long kaisiBrandId;

    private String qualityCode;

    private String qualityName;

    private String qualityOriginId;

    private String brandName;

    private String brandOriginId;

    private Integer status;

    private Date createTime;

    private Date updateTime;
}

