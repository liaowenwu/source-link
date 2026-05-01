package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 开思品牌返回对象
 */
@Data
public class KaisiBrandVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private String brandName;

    private String brandOriginId;

    private Integer status;

    private Date createTime;

    private Date updateTime;
}

