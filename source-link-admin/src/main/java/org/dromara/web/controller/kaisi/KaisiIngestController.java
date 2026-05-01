package org.dromara.web.controller.kaisi;

import org.dromara.common.core.domain.R;
import org.dromara.common.satoken.utils.LoginHelper;
import org.dromara.system.domain.bo.kaisi.KaisiSyncTaskCreateBo;
import org.dromara.system.domain.vo.kaisi.KaisiQuoteItemVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuotationVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityVo;
import org.dromara.system.service.kaisi.IKaisiBaseConfigService;
import org.dromara.system.service.kaisi.IKaisiCrawlerConfigService;
import org.dromara.system.service.kaisi.IKaisiIngestService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 开思 Python 回调接入控制器
 *
 * 说明：该控制器用于 qcpj-crawler 调用，路径保持与 Python 侧配置一致。
 */
@Validated
@RestController
@RequestMapping("/api")
public class KaisiIngestController {

    private final IKaisiIngestService kaisiIngestService;
    private final IKaisiBaseConfigService kaisiBaseConfigService;
    private final IKaisiCrawlerConfigService kaisiCrawlerConfigService;

    public KaisiIngestController(IKaisiIngestService kaisiIngestService,
                                 IKaisiBaseConfigService kaisiBaseConfigService,
                                 IKaisiCrawlerConfigService kaisiCrawlerConfigService) {
        this.kaisiIngestService = kaisiIngestService;
        this.kaisiBaseConfigService = kaisiBaseConfigService;
        this.kaisiCrawlerConfigService = kaisiCrawlerConfigService;
    }

    /**
     * 创建同步任务
     */
    @PostMapping("/sync/tasks")
    public R<Map<String, String>> createSyncTask(@RequestBody KaisiSyncTaskCreateBo bo) {
        String taskNo = kaisiIngestService.createSyncTaskNo(bo);
        Map<String, String> data = new HashMap<>(2);
        data.put("taskNo", taskNo);
        return R.ok(data);
    }

    /**
     * ingest 事件
     */
    @PostMapping("/online-orders/ingest/event")
    public R<Void> ingestEvent(
        @RequestParam(value = "taskNo", required = false) String taskNo,
        @RequestBody Map<String, Object> body
    ) {
        String event = String.valueOf(body.getOrDefault("event", ""));
        @SuppressWarnings("unchecked")
        Map<String, Object> payload = body.get("payload") instanceof Map<?, ?> ? (Map<String, Object>) body.get("payload") : new HashMap<>();
        String bodyTaskNo = String.valueOf(body.getOrDefault("taskNo", ""));
        kaisiIngestService.ingestEvent(taskNo == null || taskNo.isBlank() ? bodyTaskNo : taskNo, event, payload);
        return R.ok();
    }

    /**
     * ingest 报价单主+明细
     */
    @PostMapping("/online-orders/ingest/quotation")
    public R<Void> ingestQuotation(
        @RequestParam(value = "taskNo", required = false) String taskNo,
        @RequestBody Map<String, Object> body
    ) {
        kaisiIngestService.ingestQuotation(taskNo, body);
        return R.ok();
    }

    /**
     * 查询报价单列表（给 Python 回读）
     */
    @GetMapping("/online-orders/quotations")
    public R<List<KaisiQuotationVo>> listQuotations(@RequestParam(value = "quotationId", required = false) String quotationId) {
        return R.ok(kaisiIngestService.queryQuotations(quotationId));
    }

    /**
     * 查询报价单明细（给 Python 回读）
     */
    @GetMapping("/online-orders/quotations/{quotationId}/items")
    public R<List<KaisiQuoteItemVo>> listQuotationItems(
        @PathVariable("quotationId") String quotationId,
        @RequestParam(value = "storeId", required = false) String storeId
    ) {
        return R.ok(kaisiIngestService.queryQuotationItems(quotationId, storeId));
    }

    /**
     * 查询抓价参数（给 Python 回读）
     */
    @GetMapping("/online-orders/quotations/{quotationId}/crawler-query-params")
    public R<List<Map<String, Object>>> listCrawlerQueryParams(
        @PathVariable("quotationId") String quotationId,
        @RequestParam(value = "storeId", required = false) String storeId
    ) {
        return R.ok(kaisiIngestService.queryCrawlerQueryParams(quotationId, storeId));
    }

    /**
     * 查询开思质量字典（给 Python 回读）
     */
    @GetMapping("/kaisi/base-config/qualities/options")
    public R<List<KaisiQualityVo>> listKaisiQualityOptions() {
        return R.ok(kaisiBaseConfigService.listQualityOptions());
    }

    /**
     * 查询开思 crawler 配置（给 Python 回读）
     */
    @GetMapping("/kaisi/base-config/crawler-config")
    public R<Map<String, Object>> getKaisiCrawlerConfig(@RequestParam(value = "userId", required = false) Long userId) {
        Long resolvedUserId = userId == null ? LoginHelper.getUserId() : userId;
        return R.ok(kaisiCrawlerConfigService.getCrawlerConfig(resolvedUserId));
    }

    /**
     * 兼容旧路径：查询奔奔 crawler 配置
     */
    @GetMapping("/benben/settings/crawler-config")
    public R<Map<String, Object>> getBenbenCrawlerConfigCompat(@RequestParam(value = "userId", required = false) Long userId) {
        Long resolvedUserId = userId == null ? LoginHelper.getUserId() : userId;
        return R.ok(kaisiCrawlerConfigService.getCrawlerConfig(resolvedUserId));
    }

    /**
     * 兼容旧路径：查询质量字典
     */
    @GetMapping("/benben/settings/quality-dicts")
    public R<List<KaisiQualityVo>> getBenbenQualityDictsCompat() {
        return R.ok(kaisiBaseConfigService.listQualityOptions());
    }
}
