package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformRegion;

/**
 * 供应平台区域 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface PartCrawlerPlatformRegionMapper extends BaseMapper<PartCrawlerPlatformRegion> {
}
