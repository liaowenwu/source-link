package org.dromara.system.domain.bo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;

/**
 * 平台主表新增/修改参数
 */
@Data
public class PartCrawlerPlatformSaveBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;

    private String platformCode;

    private String platformName;

    private Integer status;
}

