package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 用户平台抓价配置查询参数
 */
@Data
public class UserPartCrawlerPlatformConfigQueryBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long userId;

    private Long platformId;

    private String platformCode;
}

