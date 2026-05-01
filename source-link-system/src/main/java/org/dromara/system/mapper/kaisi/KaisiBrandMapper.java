package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.KaisiBrand;

/**
 * 开思品牌配置 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface KaisiBrandMapper extends BaseMapper<KaisiBrand> {
}
