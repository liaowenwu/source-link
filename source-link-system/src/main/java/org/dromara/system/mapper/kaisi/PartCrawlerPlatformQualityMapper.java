package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformQuality;

/**
 * 供应平台质量 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface PartCrawlerPlatformQualityMapper extends BaseMapper<PartCrawlerPlatformQuality> {
}
