package org.dromara.system.service.kaisi;

import org.dromara.common.core.domain.R;
import org.dromara.system.domain.bo.kaisi.KaisiSyncTaskCreateBo;
import org.dromara.system.domain.vo.kaisi.KaisiQuoteItemVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuotationVo;

import java.util.List;
import java.util.Map;

/**
 * 开思 Python 回调接入服务
 */
public interface IKaisiIngestService {

    /**
     * 创建同步任务
     */
    String createSyncTaskNo(KaisiSyncTaskCreateBo bo);

    /**
     * 处理事件上报
     */
    void ingestEvent(String taskNo, String event, Map<String, Object> payload);

    /**
     * 处理报价单明细上报
     */
    void ingestQuotation(String taskNo, Map<String, Object> payload);

    /**
     * 查询报价单列表（供 Python 回读）
     */
    List<KaisiQuotationVo> queryQuotations(String quotationId);

    /**
     * 查询报价单明细（供 Python 回读）
     */
    List<KaisiQuoteItemVo> queryQuotationItems(String quotationId, String storeId);

    /**
     * 查询 crawler 查询参数（当前先返回空数组，保留接口）
     */
    List<Map<String, Object>> queryCrawlerQueryParams(String quotationId, String storeId);
}

