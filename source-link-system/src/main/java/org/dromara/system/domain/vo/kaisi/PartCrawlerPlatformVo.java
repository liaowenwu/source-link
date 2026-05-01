package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;

/**
 * 平台主表返回对象
 */
@Data
public class PartCrawlerPlatformVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private String platformCode;

    private String platformName;

    private Integer status;

    private Date createTime;

    private Date updateTime;
}

