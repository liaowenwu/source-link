package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.dromara.system.domain.kaisi.LinkKaisiQualityBrand;

/**
 * 开思质量品牌关联 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface LinkKaisiQualityBrandMapper extends BaseMapper<LinkKaisiQualityBrand> {
}
