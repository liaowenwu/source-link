package org.dromara.system.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import lombok.RequiredArgsConstructor;
import org.dromara.common.core.domain.R;
import org.dromara.common.log.annotation.Log;
import org.dromara.common.log.enums.BusinessType;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.common.web.core.BaseController;
import org.dromara.system.domain.bo.kaisi.KaisiManualPriceSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQuotationQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiWorkbenchSettingSaveBo;
import org.dromara.system.domain.vo.kaisi.KaisiDashboardVo;
import org.dromara.system.domain.vo.kaisi.KaisiHistoryPartVo;
import org.dromara.system.domain.vo.kaisi.KaisiPriceTrendPointVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuoteItemVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuotationVo;
import org.dromara.system.domain.vo.kaisi.KaisiTimelineVo;
import org.dromara.system.domain.vo.kaisi.KaisiWorkbenchSettingVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformBrandVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformQualityVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformRegionVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformSupplierVo;
import org.dromara.system.service.kaisi.IKaisiWorkbenchService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 开思工作台控制器
 */
@Validated
@RequiredArgsConstructor
@RestController
@RequestMapping("/kaisi/workbench")
public class KaisiWorkbenchController extends BaseController {

    private final IKaisiWorkbenchService kaisiWorkbenchService;

    /**
     * 首页数据
     */
    @SaCheckPermission("kaisi:workbench:dashboard")
    @GetMapping("/dashboard")
    public R<KaisiDashboardVo> dashboard() {
        return R.ok(kaisiWorkbenchService.getDashboard());
    }

    /**
     * 查询工作台设置
     */
    @SaCheckPermission("kaisi:workbench:setting:query")
    @GetMapping("/settings")
    public R<KaisiWorkbenchSettingVo> setting() {
        return R.ok(kaisiWorkbenchService.getSetting());
    }

    /**
     * 保存工作台设置
     */
    @SaCheckPermission("kaisi:workbench:setting:edit")
    @Log(title = "开思工作台设置", businessType = BusinessType.UPDATE)
    @PutMapping("/settings")
    public R<Void> saveSetting(@RequestBody KaisiWorkbenchSettingSaveBo bo) {
        kaisiWorkbenchService.saveSetting(bo);
        return R.ok();
    }

    /**
     * 查询平台质量选项
     */
    @SaCheckPermission("kaisi:workbench:setting:query")
    @GetMapping("/settings/platform-qualities")
    public R<List<PartCrawlerPlatformQualityVo>> settingQualities(@RequestParam("platformId") Long platformId) {
        return R.ok(kaisiWorkbenchService.listSettingQualities(platformId));
    }

    /**
     * 查询平台品牌选项
     */
    @SaCheckPermission("kaisi:workbench:setting:query")
    @GetMapping("/settings/platform-brands")
    public TableDataInfo<PartCrawlerPlatformBrandVo> settingBrands(
        @RequestParam("platformId") Long platformId,
        @RequestParam(value = "qualityOriginIds", required = false) String qualityOriginIds,
        @RequestParam(value = "brandName", required = false) String brandName,
        PageQuery pageQuery
    ) {
        return kaisiWorkbenchService.listSettingBrands(platformId, qualityOriginIds, brandName, pageQuery);
    }

    /**
     * 查询平台区域选项
     */
    @SaCheckPermission("kaisi:workbench:setting:query")
    @GetMapping("/settings/platform-regions")
    public R<List<PartCrawlerPlatformRegionVo>> settingRegions(@RequestParam("platformId") Long platformId) {
        return R.ok(kaisiWorkbenchService.listSettingRegions(platformId));
    }

    /**
     * 查询平台供应商选项
     */
    @SaCheckPermission("kaisi:workbench:setting:query")
    @GetMapping("/settings/platform-suppliers")
    public TableDataInfo<PartCrawlerPlatformSupplierVo> settingSuppliers(
        @RequestParam("platformId") Long platformId,
        @RequestParam(value = "supplierName", required = false) String supplierName,
        PageQuery pageQuery
    ) {
        return kaisiWorkbenchService.listSettingSuppliers(platformId, supplierName, pageQuery);
    }

    /**
     * 开启任务
     */
    @SaCheckPermission("kaisi:workbench:dashboard")
    @Log(title = "开思任务开启", businessType = BusinessType.OTHER)
    @PostMapping("/task/start")
    public R<String> startTask() {
        return R.ok(kaisiWorkbenchService.startTask());
    }

    /**
     * 停止任务
     */
    @SaCheckPermission("kaisi:workbench:dashboard")
    @Log(title = "开思任务停止", businessType = BusinessType.OTHER)
    @PostMapping("/task/stop")
    public R<Void> stopTask() {
        kaisiWorkbenchService.stopTask();
        return R.ok();
    }

    /**
     * 执行一次
     */
    @SaCheckPermission("kaisi:workbench:dashboard")
    @Log(title = "开思任务执行一次", businessType = BusinessType.OTHER)
    @PostMapping("/task/run-once")
    public R<String> runOnceTask() {
        return R.ok(kaisiWorkbenchService.runOnceTask());
    }

    /**
     * 时间线
     */
    @SaCheckPermission("kaisi:workbench:dashboard")
    @GetMapping("/timeline")
    public R<List<KaisiTimelineVo>> timeline(
        @RequestParam(value = "taskNo", required = false) String taskNo,
        @RequestParam(value = "eventType", required = false) String eventType,
        @RequestParam(value = "limit", required = false) Integer limit
    ) {
        return R.ok(kaisiWorkbenchService.listTimeline(taskNo, eventType, limit));
    }

    /**
     * 报价单列表
     */
    @SaCheckPermission("kaisi:workbench:quotation:list")
    @GetMapping("/quotations")
    public TableDataInfo<KaisiQuotationVo> quotations(KaisiQuotationQueryBo bo, PageQuery pageQuery) {
        return kaisiWorkbenchService.listQuotations(bo, pageQuery);
    }

    /**
     * 报价单明细
     */
    @SaCheckPermission("kaisi:workbench:quotation:query")
    @GetMapping("/quotations/{quotationId}/items")
    public R<List<KaisiQuoteItemVo>> quotationItems(
        @PathVariable("quotationId") String quotationId,
        @RequestParam(value = "storeId", required = false) String storeId
    ) {
        return R.ok(kaisiWorkbenchService.listQuotationItems(quotationId, storeId));
    }

    /**
     * 人工补价保存
     */
    @SaCheckPermission("kaisi:workbench:manual:edit")
    @Log(title = "开思人工补价", businessType = BusinessType.UPDATE)
    @PostMapping("/manual-price/save")
    public R<Void> saveManualPrice(@RequestBody KaisiManualPriceSaveBo bo) {
        kaisiWorkbenchService.saveManualPrice(bo);
        return R.ok();
    }

    /**
     * 手动提交
     */
    @SaCheckPermission("kaisi:workbench:quotation:submit")
    @Log(title = "开思报价单手动提交", businessType = BusinessType.OTHER)
    @PostMapping("/quotations/{quotationId}/submit")
    public R<Void> submitQuotation(
        @PathVariable("quotationId") String quotationId,
        @RequestParam(value = "storeId", required = false) String storeId
    ) {
        kaisiWorkbenchService.submitQuotation(quotationId, storeId);
        return R.ok();
    }

    /**
     * 重试
     */
    @SaCheckPermission("kaisi:workbench:quotation:retry")
    @Log(title = "开思报价单重试", businessType = BusinessType.OTHER)
    @PostMapping("/quotations/{quotationId}/retry")
    public R<Void> retryQuotation(
        @PathVariable("quotationId") String quotationId,
        @RequestParam(value = "storeId", required = false) String storeId
    ) {
        kaisiWorkbenchService.retryQuotation(quotationId, storeId);
        return R.ok();
    }

    /**
     * 历史零件统计
     */
    @SaCheckPermission("kaisi:workbench:quotation:list")
    @GetMapping("/history/parts")
    public R<List<KaisiHistoryPartVo>> historyParts(
        @RequestParam(value = "beginTime", required = false) String beginTime,
        @RequestParam(value = "endTime", required = false) String endTime,
        @RequestParam(value = "quotationId", required = false) String quotationId,
        @RequestParam(value = "partsKeyword", required = false) String partsKeyword
    ) {
        return R.ok(kaisiWorkbenchService.listHistoryParts(beginTime, endTime, quotationId, partsKeyword));
    }

    /**
     * 历史价格走势
     */
    @SaCheckPermission("kaisi:workbench:quotation:query")
    @GetMapping("/history/price-trend")
    public R<List<KaisiPriceTrendPointVo>> priceTrend(
        @RequestParam(value = "beginTime", required = false) String beginTime,
        @RequestParam(value = "endTime", required = false) String endTime,
        @RequestParam(value = "quotationId", required = false) String quotationId,
        @RequestParam(value = "partsNum") String partsNum,
        @RequestParam(value = "brandName", required = false) String brandName,
        @RequestParam(value = "partsBrandQuality", required = false) String partsBrandQuality
    ) {
        return R.ok(kaisiWorkbenchService.listPriceTrend(beginTime, endTime, quotationId, partsNum, brandName, partsBrandQuality));
    }
}
