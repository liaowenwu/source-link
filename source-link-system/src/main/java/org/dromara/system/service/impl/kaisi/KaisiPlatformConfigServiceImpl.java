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
import org.dromara.system.domain.bo.kaisi.*;
import org.dromara.system.domain.kaisi.*;
import org.dromara.system.domain.vo.kaisi.*;
import org.dromara.system.mapper.kaisi.*;
import org.dromara.system.service.kaisi.IKaisiPlatformConfigService;
import org.dromara.system.utils.kaisi.KaisiPlatformConfigConvertUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 平台配置管理服务实现
 */
@Service
@RequiredArgsConstructor
public class KaisiPlatformConfigServiceImpl implements IKaisiPlatformConfigService {

    private final PartCrawlerPlatformMapper platformMapper;
    private final PartCrawlerPlatformBrandMapper platformBrandMapper;
    private final PartCrawlerPlatformQualityMapper platformQualityMapper;
    private final PartCrawlerPlatformRegionMapper platformRegionMapper;
    private final PartCrawlerPlatformSupplierMapper platformSupplierMapper;
    private final UserPartCrawlerPlatformConfigMapper userPlatformConfigMapper;

    @Override
    public TableDataInfo<PartCrawlerPlatformVo> listPlatforms(PartCrawlerPlatformQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<PartCrawlerPlatform> lqw = Wrappers.lambdaQuery();
        lqw.like(StrUtil.isNotBlank(bo.getPlatformCode()), PartCrawlerPlatform::getPlatformCode, StrUtil.trim(bo.getPlatformCode()))
            .like(StrUtil.isNotBlank(bo.getPlatformName()), PartCrawlerPlatform::getPlatformName, StrUtil.trim(bo.getPlatformName()))
            .eq(ObjectUtil.isNotNull(bo.getStatus()), PartCrawlerPlatform::getStatus, bo.getStatus())
            .orderByAsc(PartCrawlerPlatform::getId);
        Page<PartCrawlerPlatform> page = platformMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformVoList(page.getRecords()));
    }

    @Override
    public List<PartCrawlerPlatformVo> listPlatformOptions() {
        List<PartCrawlerPlatform> rows = platformMapper.selectList(
            Wrappers.<PartCrawlerPlatform>lambdaQuery()
                .eq(PartCrawlerPlatform::getStatus, 1)
                .orderByAsc(PartCrawlerPlatform::getId)
                .last("limit 500")
        );
        return KaisiPlatformConfigConvertUtils.toPlatformVoList(rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addPlatform(PartCrawlerPlatformSaveBo bo) {
        validatePlatform(bo);
        ensurePlatformUnique(bo.getId(), bo.getPlatformCode(), bo.getPlatformName());
        PartCrawlerPlatform row = KaisiPlatformConfigConvertUtils.toPlatformEntity(bo);
        platformMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editPlatform(PartCrawlerPlatformSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("平台ID不能为空");
        }
        validatePlatform(bo);
        PartCrawlerPlatform row = requirePlatform(bo.getId());
        ensurePlatformUnique(bo.getId(), bo.getPlatformCode(), bo.getPlatformName());
        KaisiPlatformConfigConvertUtils.applyPlatform(row, bo);
        platformMapper.updateById(row);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePlatform(Long id) {
        if (id == null) {
            return;
        }
        long brandCount = platformBrandMapper.selectCount(Wrappers.<PartCrawlerPlatformBrand>lambdaQuery().eq(PartCrawlerPlatformBrand::getPlatformId, id));
        long qualityCount = platformQualityMapper.selectCount(Wrappers.<PartCrawlerPlatformQuality>lambdaQuery().eq(PartCrawlerPlatformQuality::getPlatformId, id));
        long regionCount = platformRegionMapper.selectCount(Wrappers.<PartCrawlerPlatformRegion>lambdaQuery().eq(PartCrawlerPlatformRegion::getPlatformId, id));
        long supplierCount = platformSupplierMapper.selectCount(Wrappers.<PartCrawlerPlatformSupplier>lambdaQuery().eq(PartCrawlerPlatformSupplier::getPlatformId, id));
        if (brandCount > 0 || qualityCount > 0 || regionCount > 0 || supplierCount > 0) {
            throw new ServiceException("该平台存在子配置数据，不能删除");
        }
        platformMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<PartCrawlerPlatformBrandVo> listPlatformBrands(PartCrawlerPlatformBrandQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<PartCrawlerPlatformBrand> lqw = Wrappers.lambdaQuery();
        lqw.eq(ObjectUtil.isNotNull(bo.getPlatformId()), PartCrawlerPlatformBrand::getPlatformId, bo.getPlatformId())
            .like(StrUtil.isNotBlank(bo.getBrandName()), PartCrawlerPlatformBrand::getBrandName, StrUtil.trim(bo.getBrandName()))
            .eq(StrUtil.isNotBlank(bo.getBrandOriginId()), PartCrawlerPlatformBrand::getBrandOriginId, StrUtil.trim(bo.getBrandOriginId()))
            .eq(ObjectUtil.isNotNull(bo.getStatus()), PartCrawlerPlatformBrand::getStatus, bo.getStatus())
            .orderByAsc(PartCrawlerPlatformBrand::getId);
        Page<PartCrawlerPlatformBrand> page = platformBrandMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformBrandVoList(page.getRecords()));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addPlatformBrand(PartCrawlerPlatformBrandSaveBo bo) {
        validatePlatformBrand(bo);
        requirePlatform(bo.getPlatformId());
        ensurePlatformBrandUnique(bo.getId(), bo.getPlatformId(), bo.getBrandOriginId());
        PartCrawlerPlatformBrand row = KaisiPlatformConfigConvertUtils.toPlatformBrandEntity(bo);
        platformBrandMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editPlatformBrand(PartCrawlerPlatformBrandSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("平台品牌ID不能为空");
        }
        validatePlatformBrand(bo);
        requirePlatform(bo.getPlatformId());
        PartCrawlerPlatformBrand row = platformBrandMapper.selectById(bo.getId());
        if (row == null) {
            throw new ServiceException("平台品牌不存在");
        }
        ensurePlatformBrandUnique(bo.getId(), bo.getPlatformId(), bo.getBrandOriginId());
        KaisiPlatformConfigConvertUtils.applyPlatformBrand(row, bo);
        platformBrandMapper.updateById(row);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePlatformBrand(Long id) {
        if (id == null) {
            return;
        }
        platformBrandMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<PartCrawlerPlatformQualityVo> listPlatformQualities(PartCrawlerPlatformQualityQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<PartCrawlerPlatformQuality> lqw = Wrappers.lambdaQuery();
        lqw.eq(ObjectUtil.isNotNull(bo.getPlatformId()), PartCrawlerPlatformQuality::getPlatformId, bo.getPlatformId())
            .like(StrUtil.isNotBlank(bo.getQualityCode()), PartCrawlerPlatformQuality::getQualityCode, StrUtil.trim(bo.getQualityCode()))
            .like(StrUtil.isNotBlank(bo.getQualityName()), PartCrawlerPlatformQuality::getQualityName, StrUtil.trim(bo.getQualityName()))
            .eq(StrUtil.isNotBlank(bo.getQualityOriginId()), PartCrawlerPlatformQuality::getQualityOriginId, StrUtil.trim(bo.getQualityOriginId()))
            .eq(ObjectUtil.isNotNull(bo.getStatus()), PartCrawlerPlatformQuality::getStatus, bo.getStatus())
            .orderByAsc(PartCrawlerPlatformQuality::getOrderNum)
            .orderByAsc(PartCrawlerPlatformQuality::getId);
        Page<PartCrawlerPlatformQuality> page = platformQualityMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformQualityVoList(page.getRecords()));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addPlatformQuality(PartCrawlerPlatformQualitySaveBo bo) {
        validatePlatformQuality(bo);
        requirePlatform(bo.getPlatformId());
        ensurePlatformQualityUnique(bo.getId(), bo.getPlatformId(), bo.getQualityOriginId(), bo.getQualityCode());
        PartCrawlerPlatformQuality row = KaisiPlatformConfigConvertUtils.toPlatformQualityEntity(bo);
        platformQualityMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editPlatformQuality(PartCrawlerPlatformQualitySaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("平台质量ID不能为空");
        }
        validatePlatformQuality(bo);
        requirePlatform(bo.getPlatformId());
        PartCrawlerPlatformQuality row = platformQualityMapper.selectById(bo.getId());
        if (row == null) {
            throw new ServiceException("平台质量不存在");
        }
        ensurePlatformQualityUnique(bo.getId(), bo.getPlatformId(), bo.getQualityOriginId(), bo.getQualityCode());
        KaisiPlatformConfigConvertUtils.applyPlatformQuality(row, bo);
        platformQualityMapper.updateById(row);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePlatformQuality(Long id) {
        if (id == null) {
            return;
        }
        platformQualityMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<PartCrawlerPlatformRegionVo> listPlatformRegions(PartCrawlerPlatformRegionQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<PartCrawlerPlatformRegion> lqw = Wrappers.lambdaQuery();
        lqw.eq(ObjectUtil.isNotNull(bo.getPlatformId()), PartCrawlerPlatformRegion::getPlatformId, bo.getPlatformId())
            .like(StrUtil.isNotBlank(bo.getRegionName()), PartCrawlerPlatformRegion::getRegionName, StrUtil.trim(bo.getRegionName()))
            .eq(StrUtil.isNotBlank(bo.getRegionOriginId()), PartCrawlerPlatformRegion::getRegionOriginId, StrUtil.trim(bo.getRegionOriginId()))
            .eq(ObjectUtil.isNotNull(bo.getStatus()), PartCrawlerPlatformRegion::getStatus, bo.getStatus())
            .orderByAsc(PartCrawlerPlatformRegion::getId);
        Page<PartCrawlerPlatformRegion> page = platformRegionMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformRegionVoList(page.getRecords()));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addPlatformRegion(PartCrawlerPlatformRegionSaveBo bo) {
        validatePlatformRegion(bo);
        requirePlatform(bo.getPlatformId());
        ensurePlatformRegionUnique(bo.getId(), bo.getPlatformId(), bo.getRegionOriginId());
        PartCrawlerPlatformRegion row = KaisiPlatformConfigConvertUtils.toPlatformRegionEntity(bo);
        platformRegionMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editPlatformRegion(PartCrawlerPlatformRegionSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("平台区域ID不能为空");
        }
        validatePlatformRegion(bo);
        requirePlatform(bo.getPlatformId());
        PartCrawlerPlatformRegion row = platformRegionMapper.selectById(bo.getId());
        if (row == null) {
            throw new ServiceException("平台区域不存在");
        }
        ensurePlatformRegionUnique(bo.getId(), bo.getPlatformId(), bo.getRegionOriginId());
        KaisiPlatformConfigConvertUtils.applyPlatformRegion(row, bo);
        platformRegionMapper.updateById(row);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePlatformRegion(Long id) {
        if (id == null) {
            return;
        }
        long supplierCount = platformSupplierMapper.selectCount(Wrappers.<PartCrawlerPlatformSupplier>lambdaQuery().eq(PartCrawlerPlatformSupplier::getRegionId, id));
        if (supplierCount > 0) {
            throw new ServiceException("该区域存在供应商引用，不能删除");
        }
        platformRegionMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<PartCrawlerPlatformSupplierVo> listPlatformSuppliers(PartCrawlerPlatformSupplierQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<PartCrawlerPlatformSupplier> lqw = Wrappers.lambdaQuery();
        lqw.eq(ObjectUtil.isNotNull(bo.getPlatformId()), PartCrawlerPlatformSupplier::getPlatformId, bo.getPlatformId())
            .like(StrUtil.isNotBlank(bo.getSupplierName()), PartCrawlerPlatformSupplier::getSupplierName, StrUtil.trim(bo.getSupplierName()))
            .eq(StrUtil.isNotBlank(bo.getSupplierOriginId()), PartCrawlerPlatformSupplier::getSupplierOriginId, StrUtil.trim(bo.getSupplierOriginId()))
            .eq(ObjectUtil.isNotNull(bo.getRegionId()), PartCrawlerPlatformSupplier::getRegionId, bo.getRegionId())
            .eq(ObjectUtil.isNotNull(bo.getStatus()), PartCrawlerPlatformSupplier::getStatus, bo.getStatus())
            .orderByAsc(PartCrawlerPlatformSupplier::getId);
        Page<PartCrawlerPlatformSupplier> page = platformSupplierMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformSupplierVoList(page.getRecords()));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addPlatformSupplier(PartCrawlerPlatformSupplierSaveBo bo) {
        validatePlatformSupplier(bo);
        requirePlatform(bo.getPlatformId());
        ensurePlatformSupplierUnique(bo.getId(), bo.getPlatformId(), bo.getSupplierOriginId());
        PartCrawlerPlatformSupplier row = KaisiPlatformConfigConvertUtils.toPlatformSupplierEntity(bo);
        platformSupplierMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editPlatformSupplier(PartCrawlerPlatformSupplierSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("平台供应商ID不能为空");
        }
        validatePlatformSupplier(bo);
        requirePlatform(bo.getPlatformId());
        PartCrawlerPlatformSupplier row = platformSupplierMapper.selectById(bo.getId());
        if (row == null) {
            throw new ServiceException("平台供应商不存在");
        }
        ensurePlatformSupplierUnique(bo.getId(), bo.getPlatformId(), bo.getSupplierOriginId());
        KaisiPlatformConfigConvertUtils.applyPlatformSupplier(row, bo);
        platformSupplierMapper.updateById(row);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePlatformSupplier(Long id) {
        if (id == null) {
            return;
        }
        platformSupplierMapper.deleteById(id);
    }

    @Override
    public TableDataInfo<UserPartCrawlerPlatformConfigVo> listUserPlatformConfigs(UserPartCrawlerPlatformConfigQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<UserPartCrawlerPlatformConfig> lqw = Wrappers.lambdaQuery();
        lqw.eq(ObjectUtil.isNotNull(bo.getUserId()), UserPartCrawlerPlatformConfig::getUserId, bo.getUserId())
            .eq(ObjectUtil.isNotNull(bo.getPlatformId()), UserPartCrawlerPlatformConfig::getPlatformId, bo.getPlatformId())
            .eq(StrUtil.isNotBlank(bo.getPlatformCode()), UserPartCrawlerPlatformConfig::getPlatformCode, StrUtil.trim(bo.getPlatformCode()))
            .orderByDesc(UserPartCrawlerPlatformConfig::getUpdateTime)
            .orderByDesc(UserPartCrawlerPlatformConfig::getId);
        Page<UserPartCrawlerPlatformConfig> page = userPlatformConfigMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toUserPlatformConfigVoList(page.getRecords()));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long addUserPlatformConfig(UserPartCrawlerPlatformConfigSaveBo bo) {
        validateUserPlatformConfig(bo);
        requirePlatform(bo.getPlatformId());
        ensureUserPlatformConfigUnique(bo.getId(), bo.getUserId(), bo.getPlatformCode());
        UserPartCrawlerPlatformConfig row = KaisiPlatformConfigConvertUtils.toUserPlatformConfigEntity(bo);
        userPlatformConfigMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void editUserPlatformConfig(UserPartCrawlerPlatformConfigSaveBo bo) {
        if (bo.getId() == null) {
            throw new ServiceException("用户平台配置ID不能为空");
        }
        validateUserPlatformConfig(bo);
        requirePlatform(bo.getPlatformId());
        UserPartCrawlerPlatformConfig row = userPlatformConfigMapper.selectById(bo.getId());
        if (row == null) {
            throw new ServiceException("用户平台配置不存在");
        }
        ensureUserPlatformConfigUnique(bo.getId(), bo.getUserId(), bo.getPlatformCode());
        KaisiPlatformConfigConvertUtils.applyUserPlatformConfig(row, bo);
        userPlatformConfigMapper.updateById(row);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteUserPlatformConfig(Long id) {
        if (id == null) {
            return;
        }
        userPlatformConfigMapper.deleteById(id);
    }

    private PartCrawlerPlatform requirePlatform(Long platformId) {
        PartCrawlerPlatform platform = platformMapper.selectById(platformId);
        if (platform == null) {
            throw new ServiceException("平台不存在");
        }
        return platform;
    }

    private void validatePlatform(PartCrawlerPlatformSaveBo bo) {
        if (StrUtil.isBlank(bo.getPlatformCode())) {
            throw new ServiceException("平台编码不能为空");
        }
        if (StrUtil.isBlank(bo.getPlatformName())) {
            throw new ServiceException("平台名称不能为空");
        }
    }

    private void validatePlatformBrand(PartCrawlerPlatformBrandSaveBo bo) {
        if (bo.getPlatformId() == null) {
            throw new ServiceException("平台不能为空");
        }
        if (StrUtil.isBlank(bo.getBrandName())) {
            throw new ServiceException("品牌名称不能为空");
        }
        if (StrUtil.isBlank(bo.getBrandOriginId())) {
            throw new ServiceException("品牌原始ID不能为空");
        }
    }

    private void validatePlatformQuality(PartCrawlerPlatformQualitySaveBo bo) {
        if (bo.getPlatformId() == null) {
            throw new ServiceException("平台不能为空");
        }
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

    private void validatePlatformRegion(PartCrawlerPlatformRegionSaveBo bo) {
        if (bo.getPlatformId() == null) {
            throw new ServiceException("平台不能为空");
        }
        if (StrUtil.isBlank(bo.getRegionName())) {
            throw new ServiceException("区域名称不能为空");
        }
        if (StrUtil.isBlank(bo.getRegionOriginId())) {
            throw new ServiceException("区域原始ID不能为空");
        }
    }

    private void validatePlatformSupplier(PartCrawlerPlatformSupplierSaveBo bo) {
        if (bo.getPlatformId() == null) {
            throw new ServiceException("平台不能为空");
        }
        if (StrUtil.isBlank(bo.getSupplierName())) {
            throw new ServiceException("供应商名称不能为空");
        }
        if (StrUtil.isBlank(bo.getSupplierOriginId())) {
            throw new ServiceException("供应商原始ID不能为空");
        }
    }

    private void validateUserPlatformConfig(UserPartCrawlerPlatformConfigSaveBo bo) {
        if (bo.getUserId() == null) {
            throw new ServiceException("用户ID不能为空");
        }
        if (bo.getPlatformId() == null) {
            throw new ServiceException("平台不能为空");
        }
        if (StrUtil.isBlank(bo.getPlatformCode())) {
            throw new ServiceException("平台编码不能为空");
        }
    }

    private void ensurePlatformUnique(Long selfId, String platformCode, String platformName) {
        PartCrawlerPlatform byCode = platformMapper.selectOne(
            Wrappers.<PartCrawlerPlatform>lambdaQuery().eq(PartCrawlerPlatform::getPlatformCode, StrUtil.trim(platformCode)).last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, byCode == null ? null : byCode.getId())) {
            throw new ServiceException("平台编码已存在");
        }
        PartCrawlerPlatform byName = platformMapper.selectOne(
            Wrappers.<PartCrawlerPlatform>lambdaQuery().eq(PartCrawlerPlatform::getPlatformName, StrUtil.trim(platformName)).last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, byName == null ? null : byName.getId())) {
            throw new ServiceException("平台名称已存在");
        }
    }

    private void ensurePlatformBrandUnique(Long selfId, Long platformId, String brandOriginId) {
        PartCrawlerPlatformBrand exists = platformBrandMapper.selectOne(
            Wrappers.<PartCrawlerPlatformBrand>lambdaQuery()
                .eq(PartCrawlerPlatformBrand::getPlatformId, platformId)
                .eq(PartCrawlerPlatformBrand::getBrandOriginId, StrUtil.trim(brandOriginId))
                .last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, exists == null ? null : exists.getId())) {
            throw new ServiceException("平台品牌原始ID已存在");
        }
    }

    private void ensurePlatformQualityUnique(Long selfId, Long platformId, String qualityOriginId, String qualityCode) {
        PartCrawlerPlatformQuality byOrigin = platformQualityMapper.selectOne(
            Wrappers.<PartCrawlerPlatformQuality>lambdaQuery()
                .eq(PartCrawlerPlatformQuality::getPlatformId, platformId)
                .eq(PartCrawlerPlatformQuality::getQualityOriginId, StrUtil.trim(qualityOriginId))
                .last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, byOrigin == null ? null : byOrigin.getId())) {
            throw new ServiceException("平台质量原始ID已存在");
        }
        PartCrawlerPlatformQuality byCode = platformQualityMapper.selectOne(
            Wrappers.<PartCrawlerPlatformQuality>lambdaQuery()
                .eq(PartCrawlerPlatformQuality::getPlatformId, platformId)
                .eq(PartCrawlerPlatformQuality::getQualityCode, StrUtil.trim(qualityCode))
                .last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, byCode == null ? null : byCode.getId())) {
            throw new ServiceException("平台质量编码已存在");
        }
    }

    private void ensurePlatformRegionUnique(Long selfId, Long platformId, String regionOriginId) {
        PartCrawlerPlatformRegion exists = platformRegionMapper.selectOne(
            Wrappers.<PartCrawlerPlatformRegion>lambdaQuery()
                .eq(PartCrawlerPlatformRegion::getPlatformId, platformId)
                .eq(PartCrawlerPlatformRegion::getRegionOriginId, StrUtil.trim(regionOriginId))
                .last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, exists == null ? null : exists.getId())) {
            throw new ServiceException("平台区域原始ID已存在");
        }
    }

    private void ensurePlatformSupplierUnique(Long selfId, Long platformId, String supplierOriginId) {
        PartCrawlerPlatformSupplier exists = platformSupplierMapper.selectOne(
            Wrappers.<PartCrawlerPlatformSupplier>lambdaQuery()
                .eq(PartCrawlerPlatformSupplier::getPlatformId, platformId)
                .eq(PartCrawlerPlatformSupplier::getSupplierOriginId, StrUtil.trim(supplierOriginId))
                .last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, exists == null ? null : exists.getId())) {
            throw new ServiceException("平台供应商原始ID已存在");
        }
    }

    private void ensureUserPlatformConfigUnique(Long selfId, Long userId, String platformCode) {
        UserPartCrawlerPlatformConfig exists = userPlatformConfigMapper.selectOne(
            Wrappers.<UserPartCrawlerPlatformConfig>lambdaQuery()
                .eq(UserPartCrawlerPlatformConfig::getUserId, userId)
                .eq(UserPartCrawlerPlatformConfig::getPlatformCode, StrUtil.trim(platformCode))
                .last("limit 1")
        );
        if (KaisiPlatformConfigConvertUtils.isIdConflict(selfId, exists == null ? null : exists.getId())) {
            throw new ServiceException("该用户的平台配置已存在");
        }
    }
}

