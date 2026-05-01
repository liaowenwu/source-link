package org.dromara.system.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import lombok.RequiredArgsConstructor;
import org.dromara.common.core.domain.R;
import org.dromara.common.log.annotation.Log;
import org.dromara.common.log.enums.BusinessType;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.common.web.core.BaseController;
import org.dromara.system.domain.bo.kaisi.KaisiBrandQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiBrandSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualitySaveBo;
import org.dromara.system.domain.vo.kaisi.KaisiBrandVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityBrandLinkVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityVo;
import org.dromara.system.service.kaisi.IKaisiBaseConfigService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 开思基础配置控制器
 */
@Validated
@RequiredArgsConstructor
@RestController
@RequestMapping("/kaisi/base-config")
public class KaisiBaseConfigController extends BaseController {

    private final IKaisiBaseConfigService kaisiBaseConfigService;

    /**
     * 品牌列表
     */
    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/brands")
    public TableDataInfo<KaisiBrandVo> brands(KaisiBrandQueryBo bo, PageQuery pageQuery) {
        return kaisiBaseConfigService.listBrands(bo, pageQuery);
    }

    /**
     * 品牌下拉
     */
    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/brands/options")
    public R<List<KaisiBrandVo>> brandOptions() {
        return R.ok(kaisiBaseConfigService.listBrandOptions());
    }

    /**
     * 新增品牌
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-品牌", businessType = BusinessType.INSERT)
    @PostMapping("/brands")
    public R<Long> addBrand(@RequestBody KaisiBrandSaveBo bo) {
        return R.ok(kaisiBaseConfigService.addBrand(bo));
    }

    /**
     * 修改品牌
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-品牌", businessType = BusinessType.UPDATE)
    @PutMapping("/brands")
    public R<Void> editBrand(@RequestBody KaisiBrandSaveBo bo) {
        kaisiBaseConfigService.editBrand(bo);
        return R.ok();
    }

    /**
     * 删除品牌
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-品牌", businessType = BusinessType.DELETE)
    @DeleteMapping("/brands/{id}")
    public R<Void> removeBrand(@PathVariable("id") Long id) {
        kaisiBaseConfigService.deleteBrand(id);
        return R.ok();
    }

    /**
     * 质量列表
     */
    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/qualities")
    public TableDataInfo<KaisiQualityVo> qualities(KaisiQualityQueryBo bo, PageQuery pageQuery) {
        return kaisiBaseConfigService.listQualities(bo, pageQuery);
    }

    /**
     * 质量下拉
     */
    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/qualities/options")
    public R<List<KaisiQualityVo>> qualityOptions() {
        return R.ok(kaisiBaseConfigService.listQualityOptions());
    }

    /**
     * 新增质量
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-质量", businessType = BusinessType.INSERT)
    @PostMapping("/qualities")
    public R<Long> addQuality(@RequestBody KaisiQualitySaveBo bo) {
        return R.ok(kaisiBaseConfigService.addQuality(bo));
    }

    /**
     * 修改质量
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-质量", businessType = BusinessType.UPDATE)
    @PutMapping("/qualities")
    public R<Void> editQuality(@RequestBody KaisiQualitySaveBo bo) {
        kaisiBaseConfigService.editQuality(bo);
        return R.ok();
    }

    /**
     * 删除质量
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-质量", businessType = BusinessType.DELETE)
    @DeleteMapping("/qualities/{id}")
    public R<Void> removeQuality(@PathVariable("id") Long id) {
        kaisiBaseConfigService.deleteQuality(id);
        return R.ok();
    }

    /**
     * 质量品牌关联列表
     */
    @SaCheckPermission("kaisi:base-config:query")
    @GetMapping("/quality-brand-links")
    public TableDataInfo<KaisiQualityBrandLinkVo> qualityBrandLinks(KaisiQualityBrandLinkQueryBo bo, PageQuery pageQuery) {
        return kaisiBaseConfigService.listQualityBrandLinks(bo, pageQuery);
    }

    /**
     * 新增质量品牌关联
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-质量品牌关联", businessType = BusinessType.INSERT)
    @PostMapping("/quality-brand-links")
    public R<Long> addQualityBrandLink(@RequestBody KaisiQualityBrandLinkSaveBo bo) {
        return R.ok(kaisiBaseConfigService.addQualityBrandLink(bo));
    }

    /**
     * 修改质量品牌关联
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-质量品牌关联", businessType = BusinessType.UPDATE)
    @PutMapping("/quality-brand-links")
    public R<Void> editQualityBrandLink(@RequestBody KaisiQualityBrandLinkSaveBo bo) {
        kaisiBaseConfigService.editQualityBrandLink(bo);
        return R.ok();
    }

    /**
     * 删除质量品牌关联
     */
    @SaCheckPermission("kaisi:base-config:edit")
    @Log(title = "开思基础配置-质量品牌关联", businessType = BusinessType.DELETE)
    @DeleteMapping("/quality-brand-links/{id}")
    public R<Void> removeQualityBrandLink(@PathVariable("id") Long id) {
        kaisiBaseConfigService.deleteQualityBrandLink(id);
        return R.ok();
    }
}

