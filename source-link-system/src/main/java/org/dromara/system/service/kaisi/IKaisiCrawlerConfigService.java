package org.dromara.system.service.kaisi;

import java.util.Map;

/**
 * 开思抓价配置服务
 */
public interface IKaisiCrawlerConfigService {

    /**
     * 查询 crawler 配置（兼容 Python 侧格式）
     */
    Map<String, Object> getCrawlerConfig(Long userId);
}

