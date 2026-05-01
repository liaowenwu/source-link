package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformBrand;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 供应平台品牌 Mapper
 */
@InterceptorIgnore(tenantLine = "true")
public interface PartCrawlerPlatformBrandMapper extends BaseMapper<PartCrawlerPlatformBrand> {

    /**
     * 按平台和已选择质量分页查询可选品牌
     */
    @Select({
        "<script>",
        "SELECT DISTINCT b.id, b.tenant_id, b.platform_id, b.brand_name, b.brand_origin_id, b.status,",
        " b.create_dept, b.create_by, b.create_time, b.update_by, b.update_time",
        "FROM t_part_crawler_platform_brand b",
        "<if test='qualityOriginIds != null and qualityOriginIds.size() > 0'>",
        "INNER JOIN link_kaisi_quality_brand qb ON qb.brand_origin_id = b.brand_origin_id AND qb.status = 1",
        "</if>",
        "WHERE b.platform_id = #{platformId}",
        "  AND b.status = 1",
        "<if test='brandName != null and brandName != \"\"'>",
        "  AND b.brand_name LIKE CONCAT('%', #{brandName}, '%')",
        "</if>",
        "<if test='qualityOriginIds != null and qualityOriginIds.size() > 0'>",
        "  AND qb.quality_origin_id IN",
        "  <foreach collection='qualityOriginIds' item='item' open='(' separator=',' close=')'>",
        "    #{item}",
        "  </foreach>",
        "</if>",
        "ORDER BY b.id ASC",
        "</script>"
    })
    Page<PartCrawlerPlatformBrand> selectSettingBrands(Page<PartCrawlerPlatformBrand> page,
                                                       @Param("platformId") Long platformId,
                                                       @Param("qualityOriginIds") List<String> qualityOriginIds,
                                                       @Param("brandName") String brandName);
}
