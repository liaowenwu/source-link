package org.dromara.system.utils.kaisi;

import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.system.domain.bo.kaisi.KaisiBrandSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualitySaveBo;
import org.dromara.system.domain.kaisi.KaisiBrand;
import org.dromara.system.domain.kaisi.KaisiQuality;
import org.dromara.system.domain.kaisi.LinkKaisiQualityBrand;
import org.dromara.system.domain.vo.kaisi.KaisiBrandVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityBrandLinkVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityVo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 开思基础配置对象转换工具
 */
public class KaisiBaseConfigConvertUtils {

    private KaisiBaseConfigConvertUtils() {
    }

    /**
     * BO转品牌实体
     */
    public static KaisiBrand toBrandEntity(KaisiBrandSaveBo bo) {
        KaisiBrand entity = new KaisiBrand();
        entity.setBrandName(StrUtil.trim(bo.getBrandName()));
        entity.setBrandOriginId(StrUtil.trim(bo.getBrandOriginId()));
        entity.setStatus(defaultStatus(bo.getStatus()));
        return entity;
    }

    /**
     * 覆盖品牌实体
     */
    public static void applyBrand(KaisiBrand entity, KaisiBrandSaveBo bo) {
        entity.setBrandName(StrUtil.trim(bo.getBrandName()));
        entity.setBrandOriginId(StrUtil.trim(bo.getBrandOriginId()));
        entity.setStatus(defaultStatus(bo.getStatus()));
    }

    /**
     * 品牌实体转VO
     */
    public static KaisiBrandVo toBrandVo(KaisiBrand entity) {
        KaisiBrandVo vo = new KaisiBrandVo();
        vo.setId(entity.getId());
        vo.setBrandName(entity.getBrandName());
        vo.setBrandOriginId(entity.getBrandOriginId());
        vo.setStatus(entity.getStatus());
        vo.setCreateTime(entity.getCreateTime());
        vo.setUpdateTime(entity.getUpdateTime());
        return vo;
    }

    /**
     * BO转质量实体
     */
    public static KaisiQuality toQualityEntity(KaisiQualitySaveBo bo) {
        KaisiQuality entity = new KaisiQuality();
        entity.setQualityCode(StrUtil.trim(bo.getQualityCode()));
        entity.setQualityName(StrUtil.trim(bo.getQualityName()));
        entity.setQualityOriginId(StrUtil.trim(bo.getQualityOriginId()));
        entity.setQualityType(ObjectUtil.defaultIfNull(bo.getQualityType(), 0));
        entity.setOrderNum(ObjectUtil.defaultIfNull(bo.getOrderNum(), 0));
        entity.setStatus(defaultStatus(bo.getStatus()));
        return entity;
    }

    /**
     * 覆盖质量实体
     */
    public static void applyQuality(KaisiQuality entity, KaisiQualitySaveBo bo) {
        entity.setQualityCode(StrUtil.trim(bo.getQualityCode()));
        entity.setQualityName(StrUtil.trim(bo.getQualityName()));
        entity.setQualityOriginId(StrUtil.trim(bo.getQualityOriginId()));
        entity.setQualityType(ObjectUtil.defaultIfNull(bo.getQualityType(), 0));
        entity.setOrderNum(ObjectUtil.defaultIfNull(bo.getOrderNum(), 0));
        entity.setStatus(defaultStatus(bo.getStatus()));
    }

    /**
     * 质量实体转VO
     */
    public static KaisiQualityVo toQualityVo(KaisiQuality entity) {
        KaisiQualityVo vo = new KaisiQualityVo();
        vo.setId(entity.getId());
        vo.setQualityCode(entity.getQualityCode());
        vo.setQualityName(entity.getQualityName());
        vo.setQualityOriginId(entity.getQualityOriginId());
        vo.setQualityType(entity.getQualityType());
        vo.setOrderNum(entity.getOrderNum());
        vo.setStatus(entity.getStatus());
        vo.setCreateTime(entity.getCreateTime());
        vo.setUpdateTime(entity.getUpdateTime());
        return vo;
    }

    /**
     * 构建质量品牌关联实体
     */
    public static LinkKaisiQualityBrand toQualityBrandLinkEntity(KaisiQualityBrandLinkSaveBo bo, KaisiQuality quality, KaisiBrand brand) {
        LinkKaisiQualityBrand entity = new LinkKaisiQualityBrand();
        entity.setKaisiQualityId(bo.getKaisiQualityId());
        entity.setKaisiBrandId(bo.getKaisiBrandId());
        entity.setStatus(defaultStatus(bo.getStatus()));
        applyQualityBrandSnapshot(entity, quality, brand);
        return entity;
    }

    /**
     * 覆盖质量品牌关联实体
     */
    public static void applyQualityBrandLink(LinkKaisiQualityBrand entity, KaisiQualityBrandLinkSaveBo bo, KaisiQuality quality, KaisiBrand brand) {
        entity.setKaisiQualityId(bo.getKaisiQualityId());
        entity.setKaisiBrandId(bo.getKaisiBrandId());
        entity.setStatus(defaultStatus(bo.getStatus()));
        applyQualityBrandSnapshot(entity, quality, brand);
    }

    /**
     * 质量品牌关联实体转VO
     */
    public static KaisiQualityBrandLinkVo toQualityBrandLinkVo(LinkKaisiQualityBrand entity) {
        KaisiQualityBrandLinkVo vo = new KaisiQualityBrandLinkVo();
        vo.setId(entity.getId());
        vo.setKaisiQualityId(entity.getKaisiQualityId());
        vo.setKaisiBrandId(entity.getKaisiBrandId());
        vo.setQualityCode(entity.getQualityCode());
        vo.setQualityName(entity.getQualityName());
        vo.setQualityOriginId(entity.getQualityOriginId());
        vo.setBrandName(entity.getBrandName());
        vo.setBrandOriginId(entity.getBrandOriginId());
        vo.setStatus(entity.getStatus());
        vo.setCreateTime(entity.getCreateTime());
        vo.setUpdateTime(entity.getUpdateTime());
        return vo;
    }

    /**
     * 统一状态默认值
     */
    public static Integer defaultStatus(Integer status) {
        return ObjectUtil.defaultIfNull(status, 1);
    }

    /**
     * 品牌实体列表转VO列表
     */
    public static List<KaisiBrandVo> toBrandVoList(List<KaisiBrand> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<KaisiBrandVo> result = new ArrayList<>(rows.size());
        for (KaisiBrand row : rows) {
            result.add(toBrandVo(row));
        }
        return result;
    }

    /**
     * 质量实体列表转VO列表
     */
    public static List<KaisiQualityVo> toQualityVoList(List<KaisiQuality> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<KaisiQualityVo> result = new ArrayList<>(rows.size());
        for (KaisiQuality row : rows) {
            result.add(toQualityVo(row));
        }
        return result;
    }

    /**
     * 质量品牌关联实体列表转VO列表
     */
    public static List<KaisiQualityBrandLinkVo> toQualityBrandLinkVoList(List<LinkKaisiQualityBrand> rows) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        List<KaisiQualityBrandLinkVo> result = new ArrayList<>(rows.size());
        for (LinkKaisiQualityBrand row : rows) {
            result.add(toQualityBrandLinkVo(row));
        }
        return result;
    }

    /**
     * 构建分页返回
     */
    public static <T> TableDataInfo<T> buildTable(Page<?> source, List<T> records) {
        Page<T> voPage = new Page<>(source.getCurrent(), source.getSize(), source.getTotal());
        voPage.setRecords(records);
        return TableDataInfo.build(voPage);
    }

    /**
     * 判定主键是否冲突
     */
    public static boolean isIdConflict(Long selfId, Long targetId) {
        return targetId != null && (selfId == null || !targetId.equals(selfId));
    }

    /**
     * 从品牌与质量主数据回填冗余字段
     */
    private static void applyQualityBrandSnapshot(LinkKaisiQualityBrand entity, KaisiQuality quality, KaisiBrand brand) {
        entity.setQualityCode(quality.getQualityCode());
        entity.setQualityName(quality.getQualityName());
        entity.setQualityOriginId(quality.getQualityOriginId());
        entity.setBrandName(brand.getBrandName());
        entity.setBrandOriginId(brand.getBrandOriginId());
    }
}
