package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.KaisiQuality;

/**
 * 开思质量配置 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface KaisiQualityMapper extends BaseMapper<KaisiQuality> {
}
