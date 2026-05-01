package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 平台质量返回对象
 */
@Data
public class PartCrawlerPlatformQualityVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private Long platformId;

    private String qualityCode;

    private String qualityName;

    private String qualityOriginId;

    private Integer qualityType;

    private Integer orderNum;

    private Integer status;

    private Date createTime;

    private Date updateTime;
}

