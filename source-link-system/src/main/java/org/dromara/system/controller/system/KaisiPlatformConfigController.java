package org.dromara.system.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import lombok.RequiredArgsConstructor;
import org.dromara.common.core.domain.R;
import org.dromara.common.log.annotation.Log;
import org.dromara.common.log.enums.BusinessType;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.common.web.core.BaseController;
import org.dromara.system.domain.bo.kaisi.*;
import org.dromara.system.domain.vo.kaisi.*;
import org.dromara.system.service.kaisi.IKaisiPlatformConfigService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 平台配置管理控制器
 */
@Validated
@RequiredArgsConstructor
@RestController
@RequestMapping("/kaisi/base-config")
public class KaisiPlatformConfigController extends BaseController {

    private final IKaisiPlatformConfigService kaisiPlatformConfigService;

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/platforms")
    public TableDataInfo<PartCrawlerPlatformVo> platforms(PartCrawlerPlatformQueryBo bo, PageQuery pageQuery) {
        return kaisiPlatformConfigService.listPlatforms(bo, pageQuery);
    }

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/platforms/options")
    public R<List<PartCrawlerPlatformVo>> platformOptions() {
        return R.ok(kaisiPlatformConfigService.listPlatformOptions());
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台主表", businessType = BusinessType.INSERT)
    @PostMapping("/platforms")
    public R<Long> addPlatform(@RequestBody PartCrawlerPlatformSaveBo bo) {
        return R.ok(kaisiPlatformConfigService.addPlatform(bo));
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台主表", businessType = BusinessType.UPDATE)
    @PutMapping("/platforms")
    public R<Void> editPlatform(@RequestBody PartCrawlerPlatformSaveBo bo) {
        kaisiPlatformConfigService.editPlatform(bo);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台主表", businessType = BusinessType.DELETE)
    @DeleteMapping("/platforms/{id}")
    public R<Void> removePlatform(@PathVariable("id") Long id) {
        kaisiPlatformConfigService.deletePlatform(id);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/platform-brands")
    public TableDataInfo<PartCrawlerPlatformBrandVo> platformBrands(PartCrawlerPlatformBrandQueryBo bo, PageQuery pageQuery) {
        return kaisiPlatformConfigService.listPlatformBrands(bo, pageQuery);
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台品牌", businessType = BusinessType.INSERT)
    @PostMapping("/platform-brands")
    public R<Long> addPlatformBrand(@RequestBody PartCrawlerPlatformBrandSaveBo bo) {
        return R.ok(kaisiPlatformConfigService.addPlatformBrand(bo));
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台品牌", businessType = BusinessType.UPDATE)
    @PutMapping("/platform-brands")
    public R<Void> editPlatformBrand(@RequestBody PartCrawlerPlatformBrandSaveBo bo) {
        kaisiPlatformConfigService.editPlatformBrand(bo);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台品牌", businessType = BusinessType.DELETE)
    @DeleteMapping("/platform-brands/{id}")
    public R<Void> removePlatformBrand(@PathVariable("id") Long id) {
        kaisiPlatformConfigService.deletePlatformBrand(id);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/platform-qualities")
    public TableDataInfo<PartCrawlerPlatformQualityVo> platformQualities(PartCrawlerPlatformQualityQueryBo bo, PageQuery pageQuery) {
        return kaisiPlatformConfigService.listPlatformQualities(bo, pageQuery);
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台质量", businessType = BusinessType.INSERT)
    @PostMapping("/platform-qualities")
    public R<Long> addPlatformQuality(@RequestBody PartCrawlerPlatformQualitySaveBo bo) {
        return R.ok(kaisiPlatformConfigService.addPlatformQuality(bo));
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台质量", businessType = BusinessType.UPDATE)
    @PutMapping("/platform-qualities")
    public R<Void> editPlatformQuality(@RequestBody PartCrawlerPlatformQualitySaveBo bo) {
        kaisiPlatformConfigService.editPlatformQuality(bo);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台质量", businessType = BusinessType.DELETE)
    @DeleteMapping("/platform-qualities/{id}")
    public R<Void> removePlatformQuality(@PathVariable("id") Long id) {
        kaisiPlatformConfigService.deletePlatformQuality(id);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/platform-regions")
    public TableDataInfo<PartCrawlerPlatformRegionVo> platformRegions(PartCrawlerPlatformRegionQueryBo bo, PageQuery pageQuery) {
        return kaisiPlatformConfigService.listPlatformRegions(bo, pageQuery);
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台区域", businessType = BusinessType.INSERT)
    @PostMapping("/platform-regions")
    public R<Long> addPlatformRegion(@RequestBody PartCrawlerPlatformRegionSaveBo bo) {
        return R.ok(kaisiPlatformConfigService.addPlatformRegion(bo));
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台区域", businessType = BusinessType.UPDATE)
    @PutMapping("/platform-regions")
    public R<Void> editPlatformRegion(@RequestBody PartCrawlerPlatformRegionSaveBo bo) {
        kaisiPlatformConfigService.editPlatformRegion(bo);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台区域", businessType = BusinessType.DELETE)
    @DeleteMapping("/platform-regions/{id}")
    public R<Void> removePlatformRegion(@PathVariable("id") Long id) {
        kaisiPlatformConfigService.deletePlatformRegion(id);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/platform-suppliers")
    public TableDataInfo<PartCrawlerPlatformSupplierVo> platformSuppliers(PartCrawlerPlatformSupplierQueryBo bo, PageQuery pageQuery) {
        return kaisiPlatformConfigService.listPlatformSuppliers(bo, pageQuery);
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台供应商", businessType = BusinessType.INSERT)
    @PostMapping("/platform-suppliers")
    public R<Long> addPlatformSupplier(@RequestBody PartCrawlerPlatformSupplierSaveBo bo) {
        return R.ok(kaisiPlatformConfigService.addPlatformSupplier(bo));
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台供应商", businessType = BusinessType.UPDATE)
    @PutMapping("/platform-suppliers")
    public R<Void> editPlatformSupplier(@RequestBody PartCrawlerPlatformSupplierSaveBo bo) {
        kaisiPlatformConfigService.editPlatformSupplier(bo);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-平台供应商", businessType = BusinessType.DELETE)
    @DeleteMapping("/platform-suppliers/{id}")
    public R<Void> removePlatformSupplier(@PathVariable("id") Long id) {
        kaisiPlatformConfigService.deletePlatformSupplier(id);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/user-platform-configs")
    public TableDataInfo<UserPartCrawlerPlatformConfigVo> userPlatformConfigs(UserPartCrawlerPlatformConfigQueryBo bo, PageQuery pageQuery) {
        return kaisiPlatformConfigService.listUserPlatformConfigs(bo, pageQuery);
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-用户抓价配置", businessType = BusinessType.INSERT)
    @PostMapping("/user-platform-configs")
    public R<Long> addUserPlatformConfig(@RequestBody UserPartCrawlerPlatformConfigSaveBo bo) {
        return R.ok(kaisiPlatformConfigService.addUserPlatformConfig(bo));
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-用户抓价配置", businessType = BusinessType.UPDATE)
    @PutMapping("/user-platform-configs")
    public R<Void> editUserPlatformConfig(@RequestBody UserPartCrawlerPlatformConfigSaveBo bo) {
        kaisiPlatformConfigService.editUserPlatformConfig(bo);
        return R.ok();
    }

    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思平台配置-用户抓价配置", businessType = BusinessType.DELETE)
    @DeleteMapping("/user-platform-configs/{id}")
    public R<Void> removeUserPlatformConfig(@PathVariable("id") Long id) {
        kaisiPlatformConfigService.deleteUserPlatformConfig(id);
        return R.ok();
    }
}

