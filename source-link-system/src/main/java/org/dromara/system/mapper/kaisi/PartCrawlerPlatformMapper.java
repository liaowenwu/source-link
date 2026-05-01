package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.PartCrawlerPlatform;

/**
 * 供应平台主表 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface PartCrawlerPlatformMapper extends BaseMapper<PartCrawlerPlatform> {
}
