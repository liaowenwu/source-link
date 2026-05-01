package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 平台区域返回对象
 */
@Data
public class PartCrawlerPlatformRegionVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long platformId;

    private String regionName;

    private String regionOriginId;

    private Integer status;

    private Date createTime;

    private Date updateTime;
}

