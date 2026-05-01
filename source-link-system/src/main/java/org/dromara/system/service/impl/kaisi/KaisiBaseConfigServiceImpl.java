package org.dromara.system.service.impl.kaisi;

import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.dromara.common.core.exception.ServiceException;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.system.domain.bo.kaisi.KaisiBrandQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiBrandSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualitySaveBo;
import org.dromara.system.domain.kaisi.KaisiBrand;
import org.dromara.system.domain.kaisi.KaisiQuality;
import org.dromara.system.domain.kaisi.LinkKaisiQualityBrand;
import org.dromara.system.domain.vo.kaisi.KaisiBrandVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityBrandLinkVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityVo;
import org.dromara.system.mapper.kaisi.KaisiBrandMapper;
import org.dromara.system.mapper.kaisi.KaisiQualityMapper;
import org.dromara.system.mapper.kaisi.LinkKaisiQualityBrandMapper;
import org.dromara.system.service.kaisi.IKaisiBaseConfigService;
import org.dromara.system.utils.kaisi.KaisiBaseConfigConvertUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 开思基础配置服务实现
 */
@Service
@RequiredArgsConstructor
public class KaisiBaseConfigServiceImpl implements IKaisiBaseConfigService {

    private final KaisiBrandMapper kaisiBrandMapper;
    private final KaisiQualityMapper kaisiQualityMapper;
    private final LinkKaisiQualityBrandMapper qualityBrandMapper;

    @Override
    public TableDataInfo<KaisiBrandVo> listBrands(KaisiBrandQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<KaisiBrand> lqw = Wrappers.lambdaQuery();
        lqw.like(StrUtil.isNotBlank(bo.getBrandName()), KaisiBrand::getBrandName, StrUtil.trim(bo.getBrandName()))
            .eq(StrUtil.isNotBlank(bo.getBrandOriginId()), KaisiBrand::getBrandOriginId, StrUtil.trim(bo.getBrandOriginId()))
            .eq(ObjectUtil.isNotNull(bo.getStatus()), KaisiBrand::getStatus, bo.getStatus())
            .orderByAsc(KaisiBrand::getBrandName)
            .orderByDesc(KaisiBrand::getId);
        Page<KaisiBrand> page = kaisiBrandMapper.selectPage(pageQuery.build(), lqw);
        return KaisiBaseConfigConvertUtils.buildTable(page, KaisiBaseConfigConvertUtils.toBrandVoList(page.getRecords()));
    }

    @Override
    public List<KaisiBrandVo> listBrandOptions() {
        List<KaisiBrand> rows = kaisiBrandMapper.selectList(
            Wrappers.<KaisiBrand>lambdaQuery()
                .eq(KaisiBrand::getStatus, 1)
                .orderByAsc(KaisiBrand::getBrandName)
                .orderByDesc(KaisiBrand::getId)
                .last("limit 1000")
        );
        return KaisiBaseConfigConvertUtils.toBrandVoList(rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addBrand(KaisiBrandSaveBo bo) {
        validateBrandSaveBo(bo);
        ensureBrandUnique(bo.getId(), bo.getBrandOriginId(), bo.getBrandName());
        KaisiBrand entity = KaisiBaseConfigConvertUtils.toBrandEntity(bo);
        kaisiBrandMapper.insert(entity);
        return entity.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editBrand(KaisiBrandSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("品牌ID不能为空");
        }
        validateBrandSaveBo(bo);
        KaisiBrand current = kaisiBrandMapper.selectById(bo.getId());
        if (current == null) {
            throw new ServiceException("品牌不存在");
        }
        ensureBrandUnique(bo.getId(), bo.getBrandOriginId(), bo.getBrandName());
        KaisiBaseConfigConvertUtils.applyBrand(current, bo);
        kaisiBrandMapper.updateById(current);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteBrand(Long id) {
        if (id == null) {
            return;
        }
        Long linkCount = qualityBrandMapper.selectCount(
            Wrappers.<LinkKaisiQualityBrand>lambdaQuery().eq(LinkKaisiQualityBrand::getKaisiBrandId, id)
        );
        if (ObjectUtil.defaultIfNull(linkCount, 0L) > 0) {
            throw new ServiceException("该品牌已被质量关联引用，不能删除");
        }
        kaisiBrandMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<KaisiQualityVo> listQualities(KaisiQualityQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<KaisiQuality> lqw = Wrappers.lambdaQuery();
        lqw.like(StrUtil.isNotBlank(bo.getQualityCode()), KaisiQuality::getQualityCode, StrUtil.trim(bo.getQualityCode()))
            .like(StrUtil.isNotBlank(bo.getQualityName()), KaisiQuality::getQualityName, StrUtil.trim(bo.getQualityName()))
            .eq(StrUtil.isNotBlank(bo.getQualityOriginId()), KaisiQuality::getQualityOriginId, StrUtil.trim(bo.getQualityOriginId()))
            .eq(ObjectUtil.isNotNull(bo.getStatus()), KaisiQuality::getStatus, bo.getStatus())
            .orderByAsc(KaisiQuality::getOrderNum)
            .orderByAsc(KaisiQuality::getQualityCode)
            .orderByDesc(KaisiQuality::getId);
        Page<KaisiQuality> page = kaisiQualityMapper.selectPage(pageQuery.build(), lqw);
        return KaisiBaseConfigConvertUtils.buildTable(page, KaisiBaseConfigConvertUtils.toQualityVoList(page.getRecords()));
    }

    @Override
    public List<KaisiQualityVo> listQualityOptions() {
        List<KaisiQuality> rows = kaisiQualityMapper.selectList(
            Wrappers.<KaisiQuality>lambdaQuery()
                .eq(KaisiQuality::getStatus, 1)
                .orderByAsc(KaisiQuality::getOrderNum)
                .orderByAsc(KaisiQuality::getQualityCode)
                .orderByDesc(KaisiQuality::getId)
                .last("limit 1000")
        );
        return KaisiBaseConfigConvertUtils.toQualityVoList(rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addQuality(KaisiQualitySaveBo bo) {
        validateQualitySaveBo(bo);
        ensureQualityUnique(bo.getId(), bo.getQualityOriginId(), bo.getQualityCode());
        KaisiQuality entity = KaisiBaseConfigConvertUtils.toQualityEntity(bo);
        kaisiQualityMapper.insert(entity);
        return entity.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editQuality(KaisiQualitySaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("质量ID不能为空");
        }
        validateQualitySaveBo(bo);
        KaisiQuality current = kaisiQualityMapper.selectById(bo.getId());
        if (current == null) {
            throw new ServiceException("质量不存在");
        }
        ensureQualityUnique(bo.getId(), bo.getQualityOriginId(), bo.getQualityCode());
        KaisiBaseConfigConvertUtils.applyQuality(current, bo);
        kaisiQualityMapper.updateById(current);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteQuality(Long id) {
        if (id == null) {
            return;
        }
        Long linkCount = qualityBrandMapper.selectCount(
            Wrappers.<LinkKaisiQualityBrand>lambdaQuery().eq(LinkKaisiQualityBrand::getKaisiQualityId, id)
        );
        if (ObjectUtil.defaultIfNull(linkCount, 0L) > 0) {
            throw new ServiceException("该质量已被品牌关联引用，不能删除");
        }
        kaisiQualityMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<KaisiQualityBrandLinkVo> listQualityBrandLinks(KaisiQualityBrandLinkQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<LinkKaisiQualityBrand> lqw = Wrappers.lambdaQuery();
        lqw.eq(ObjectUtil.isNotNull(bo.getKaisiQualityId()), LinkKaisiQualityBrand::getKaisiQualityId, bo.getKaisiQualityId())
            .eq(ObjectUtil.isNotNull(bo.getKaisiBrandId()), LinkKaisiQualityBrand::getKaisiBrandId, bo.getKaisiBrandId())
            .eq(ObjectUtil.isNotNull(bo.getStatus()), LinkKaisiQualityBrand::getStatus, bo.getStatus())
            .and(StrUtil.isNotBlank(bo.getKeyword()), wrapper -> wrapper
                .like(LinkKaisiQualityBrand::getQualityName, StrUtil.trim(bo.getKeyword()))
                .or()
                .like(LinkKaisiQualityBrand::getBrandName, StrUtil.trim(bo.getKeyword())))
            .orderByAsc(LinkKaisiQualityBrand::getQualityCode)
            .orderByAsc(LinkKaisiQualityBrand::getBrandName)
            .orderByDesc(LinkKaisiQualityBrand::getId);
        Page<LinkKaisiQualityBrand> page = qualityBrandMapper.selectPage(pageQuery.build(), lqw);
        return KaisiBaseConfigConvertUtils.buildTable(page, KaisiBaseConfigConvertUtils.toQualityBrandLinkVoList(page.getRecords()));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addQualityBrandLink(KaisiQualityBrandLinkSaveBo bo) {
        validateQualityBrandLinkSaveBo(bo);
        KaisiQuality quality = requireQuality(bo.getKaisiQualityId());
        KaisiBrand brand = requireBrand(bo.getKaisiBrandId());
        ensureQualityBrandLinkUnique(bo.getId(), bo.getKaisiQualityId(), bo.getKaisiBrandId());
        LinkKaisiQualityBrand entity = KaisiBaseConfigConvertUtils.toQualityBrandLinkEntity(bo, quality, brand);
        qualityBrandMapper.insert(entity);
        return entity.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editQualityBrandLink(KaisiQualityBrandLinkSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("关联ID不能为空");
        }
        validateQualityBrandLinkSaveBo(bo);
        LinkKaisiQualityBrand current = qualityBrandMapper.selectById(bo.getId());
        if (current == null) {
            throw new ServiceException("关联关系不存在");
        }
        KaisiQuality quality = requireQuality(bo.getKaisiQualityId());
        KaisiBrand brand = requireBrand(bo.getKaisiBrandId());
        ensureQualityBrandLinkUnique(bo.getId(), bo.getKaisiQualityId(), bo.getKaisiBrandId());
        KaisiBaseConfigConvertUtils.applyQualityBrandLink(current, bo, quality, brand);
        qualityBrandMapper.updateById(current);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteQualityBrandLink(Long id) {
        if (id == null) {
            return;
        }
        qualityBrandMapper.deleteById(id);
    }

    private void validateBrandSaveBo(KaisiBrandSaveBo bo) {
        if (StrUtil.isBlank(bo.getBrandName())) {
            throw new ServiceException("品牌名称不能为空");
        }
        if (StrUtil.isBlank(bo.getBrandOriginId())) {
            throw new ServiceException("品牌原始ID不能为空");
        }
    }

    private void validateQualitySaveBo(KaisiQualitySaveBo bo) {
        if (StrUtil.isBlank(bo.getQualityCode())) {
            throw new ServiceException("质量编码不能为空");
        }
        if (StrUtil.isBlank(bo.getQualityName())) {
            throw new ServiceException("质量名称不能为空");
        }
        if (StrUtil.isBlank(bo.getQualityOriginId())) {
            throw new ServiceException("质量原始ID不能为空");
        }
    }

    private void validateQualityBrandLinkSaveBo(KaisiQualityBrandLinkSaveBo bo) {
        if (bo.getKaisiQualityId() == null) {
            throw new ServiceException("质量不能为空");
        }
        if (bo.getKaisiBrandId() == null) {
            throw new ServiceException("品牌不能为空");
        }
    }

    private void ensureBrandUnique(Long selfId, String brandOriginId, String brandName) {
        KaisiBrand byOriginId = kaisiBrandMapper.selectOne(
            Wrappers.<KaisiBrand>lambdaQuery().eq(KaisiBrand::getBrandOriginId, StrUtil.trim(brandOriginId)).last("limit 1")
        );
        if (KaisiBaseConfigConvertUtils.isIdConflict(selfId, byOriginId == null ? null : byOriginId.getId())) {
            throw new ServiceException("品牌原始ID已存在");
        }
        KaisiBrand byName = kaisiBrandMapper.selectOne(
            Wrappers.<KaisiBrand>lambdaQuery().eq(KaisiBrand::getBrandName, StrUtil.trim(brandName)).last("limit 1")
        );
        if (KaisiBaseConfigConvertUtils.isIdConflict(selfId, byName == null ? null : byName.getId())) {
            throw new ServiceException("品牌名称已存在");
        }
    }

    private void ensureQualityUnique(Long selfId, String qualityOriginId, String qualityCode) {
        KaisiQuality byOriginId = kaisiQualityMapper.selectOne(
            Wrappers.<KaisiQuality>lambdaQuery().eq(KaisiQuality::getQualityOriginId, StrUtil.trim(qualityOriginId)).last("limit 1")
        );
        if (KaisiBaseConfigConvertUtils.isIdConflict(selfId, byOriginId == null ? null : byOriginId.getId())) {
            throw new ServiceException("质量原始ID已存在");
        }
        KaisiQuality byCode = kaisiQualityMapper.selectOne(
            Wrappers.<KaisiQuality>lambdaQuery().eq(KaisiQuality::getQualityCode, StrUtil.trim(qualityCode)).last("limit 1")
        );
        if (KaisiBaseConfigConvertUtils.isIdConflict(selfId, byCode == null ? null : byCode.getId())) {
            throw new ServiceException("质量编码已存在");
        }
    }

    private void ensureQualityBrandLinkUnique(Long selfId, Long qualityId, Long brandId) {
        LinkKaisiQualityBrand exists = qualityBrandMapper.selectOne(
            Wrappers.<LinkKaisiQualityBrand>lambdaQuery()
                .eq(LinkKaisiQualityBrand::getKaisiQualityId, qualityId)
                .eq(LinkKaisiQualityBrand::getKaisiBrandId, brandId)
                .last("limit 1")
        );
        if (KaisiBaseConfigConvertUtils.isIdConflict(selfId, exists == null ? null : exists.getId())) {
            throw new ServiceException("该质量与品牌关联已存在");
        }
    }

    private KaisiBrand requireBrand(Long brandId) {
        KaisiBrand brand = kaisiBrandMapper.selectById(brandId);
        if (brand == null) {
            throw new ServiceException("品牌不存在");
        }
        return brand;
    }

    private KaisiQuality requireQuality(Long qualityId) {
        KaisiQuality quality = kaisiQualityMapper.selectById(qualityId);
        if (quality == null) {
            throw new ServiceException("质量不存在");
        }
        return quality;
    }

}
