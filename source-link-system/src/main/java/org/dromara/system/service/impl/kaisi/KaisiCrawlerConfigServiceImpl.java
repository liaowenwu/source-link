package org.dromara.system.service.impl.kaisi;

import cn.hutool.core.util.StrUtil;
import lombok.RequiredArgsConstructor;
import org.dromara.system.mapper.kaisi.KaisiCrawlerConfigMapper;
import org.dromara.system.service.kaisi.IKaisiCrawlerConfigService;
import org.dromara.system.utils.kaisi.KaisiCrawlerConfigBuildUtils;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Map;

/**
 * 开思抓价配置服务实现
 */
@Service
@RequiredArgsConstructor
public class KaisiCrawlerConfigServiceImpl implements IKaisiCrawlerConfigService {

    private final KaisiCrawlerConfigMapper crawlerConfigMapper;

    @Override
    public Map<String, Object> getCrawlerConfig(Long userId) {
        Map<String, Object> globalConfig = crawlerConfigMapper.selectUserGlobalConfig(userId);
        Map<String, Object> benbenConfig = loadSinglePlatformConfig(userId, "benben");
        Map<String, Object> robotConfig = loadSinglePlatformConfig(userId, "robot");
        return KaisiCrawlerConfigBuildUtils.buildCrawlerConfigRoot(globalConfig, benbenConfig, robotConfig);
    }

    /**
     * 读取单个平台配置并组装为 Python 可消费结构
     */
    private Map<String, Object> loadSinglePlatformConfig(Long userId, String platformCode) {
        String normalizedPlatformCode = StrUtil.blankToDefault(platformCode, StrUtil.EMPTY);
        Map<String, Object> mainConfig = crawlerConfigMapper.selectUserPlatformConfig(userId, normalizedPlatformCode);
        if (mainConfig == null) {
            mainConfig = Collections.emptyMap();
        }
        return KaisiCrawlerConfigBuildUtils.buildPlatformConfig(
            normalizedPlatformCode,
            mainConfig
        );
    }
}
