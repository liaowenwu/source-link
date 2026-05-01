package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformSupplier;

/**
 * 供应平台供应商 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface PartCrawlerPlatformSupplierMapper extends BaseMapper<PartCrawlerPlatformSupplier> {
}
