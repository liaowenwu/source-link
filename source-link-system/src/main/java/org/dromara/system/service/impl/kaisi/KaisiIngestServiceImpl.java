package org.dromara.system.service.impl.kaisi;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.date.DateUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import lombok.RequiredArgsConstructor;
import org.dromara.system.domain.bo.kaisi.KaisiSyncTaskCreateBo;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuoteItem;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuotation;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTask;
import org.dromara.system.domain.vo.kaisi.KaisiQuoteItemVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuotationVo;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiExecutionLogMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiQuoteItemMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiQuotationMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiSubmitItemMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiTaskLogMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiTaskMapper;
import org.dromara.system.service.kaisi.IKaisiIngestService;
import org.dromara.system.utils.kaisi.KaisiEventTypeConstants;
import org.dromara.system.utils.kaisi.KaisiIngestConvertUtils;
import org.dromara.system.utils.kaisi.KaisiMapUtils;
import org.dromara.system.utils.kaisi.KaisiSseUtils;
import org.dromara.system.utils.kaisi.KaisiWorkbenchConvertUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 开思 Python 回调处理实现
 */
@Service
@RequiredArgsConstructor
public class KaisiIngestServiceImpl implements IKaisiIngestService {

    private final OnlineOrderKaisiTaskMapper taskMapper;
    private final OnlineOrderKaisiTaskLogMapper taskLogMapper;
    private final OnlineOrderKaisiQuotationMapper quotationMapper;
    private final OnlineOrderKaisiQuoteItemMapper quoteItemMapper;
    private final OnlineOrderKaisiExecutionLogMapper executionLogMapper;
    private final OnlineOrderKaisiSubmitItemMapper submitItemMapper;

    @Override
    public String createSyncTaskNo(KaisiSyncTaskCreateBo bo) {
        String taskNo = "SYNC" + DateUtil.format(new Date(), "yyyyMMddHHmmss") + IdUtil.fastSimpleUUID().substring(0, 6).toUpperCase();
        Map<String, Object> payload = new HashMap<>(8);
        payload.put("taskType", bo.getTaskType());
        payload.put("bizType", bo.getBizType());
        payload.put("triggerBy", bo.getTriggerBy());
        payload.put("totalCount", bo.getTotalCount());
        OnlineOrderKaisiTask task = KaisiIngestConvertUtils.buildInitTask(taskNo, payload, "frontend");
        taskMapper.insert(task);
        return taskNo;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void ingestEvent(String taskNo, String event, Map<String, Object> payload) {
        String normalizedTaskNo = StrUtil.blankToDefault(taskNo, "UNKNOWN");
        String normalizedEvent = StrUtil.blankToDefault(event, KaisiEventTypeConstants.TASK_LOG);
        Map<String, Object> eventPayload = ObjectUtil.defaultIfNull(payload, Collections.emptyMap());

        OnlineOrderKaisiTask task = ensureTask(normalizedTaskNo, eventPayload);
        appendTaskLog(normalizedTaskNo, normalizedEvent, eventPayload);
        updateTaskByEvent(task, normalizedEvent, eventPayload);
        syncQuotationByEvent(normalizedTaskNo, normalizedEvent, eventPayload);

        String topic = "kaisi.task";
        String quotationId = KaisiMapUtils.getString(eventPayload, "quotationId");
        if (StrUtil.isNotBlank(quotationId)) {
            topic = "kaisi.quotation." + quotationId;
        }
        KaisiSseUtils.publish(topic, normalizedEvent, normalizedTaskNo, eventPayload);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void ingestQuotation(String taskNo, Map<String, Object> payload) {
        String normalizedTaskNo = StrUtil.blankToDefault(taskNo, "UNKNOWN");
        Map<String, Object> body = ObjectUtil.defaultIfNull(payload, Collections.emptyMap());
        ensureTask(normalizedTaskNo, body);

        String quotationId = KaisiMapUtils.getString(body, "quotationId");
        String storeId = KaisiMapUtils.getString(body, "storeId");
        if (StrUtil.isBlank(quotationId)) {
            return;
        }

        OnlineOrderKaisiQuotation quotation = upsertQuotation(normalizedTaskNo, body, quotationId, storeId);
        syncQuotationItems(quotationId, storeId, KaisiMapUtils.getMapList(body, "items"));
        appendExecutionLog(normalizedTaskNo, body, "TASK_ONLINE_ORDER_QUOTATION", "INFO");

        Map<String, Object> pushPayload = new HashMap<>(body);
        pushPayload.put("quotationId", quotationId);
        pushPayload.put("storeId", storeId);
        KaisiSseUtils.publish("kaisi.quotation." + quotationId, KaisiEventTypeConstants.TASK_ONLINE_ORDER_QUOTATION, normalizedTaskNo, pushPayload);
    }

    @Override
    public List<KaisiQuotationVo> queryQuotations(String quotationId) {
        LambdaQueryWrapper<OnlineOrderKaisiQuotation> lqw = Wrappers.lambdaQuery();
        lqw.eq(StrUtil.isNotBlank(quotationId), OnlineOrderKaisiQuotation::getQuotationId, quotationId)
            .orderByDesc(OnlineOrderKaisiQuotation::getUpdateTime)
            .last("limit 200");
        List<OnlineOrderKaisiQuotation> rows = quotationMapper.selectList(lqw);
        if (CollUtil.isEmpty(rows)) {
            return Collections.emptyList();
        }
        List<KaisiQuotationVo> result = new ArrayList<>(rows.size());
        for (OnlineOrderKaisiQuotation row : rows) {
            result.add(KaisiWorkbenchConvertUtils.toQuotationVo(row));
        }
        return result;
    }

    @Override
    public List<KaisiQuoteItemVo> queryQuotationItems(String quotationId, String storeId) {
        LambdaQueryWrapper<OnlineOrderKaisiQuoteItem> lqw = Wrappers.lambdaQuery();
        lqw.eq(OnlineOrderKaisiQuoteItem::getQuotationId, quotationId)
            .eq(StrUtil.isNotBlank(storeId), OnlineOrderKaisiQuoteItem::getStoreId, storeId)
            .orderByAsc(OnlineOrderKaisiQuoteItem::getId);
        List<OnlineOrderKaisiQuoteItem> rows = quoteItemMapper.selectList(lqw);
        if (CollUtil.isEmpty(rows)) {
            return Collections.emptyList();
        }
        List<KaisiQuoteItemVo> result = new ArrayList<>(rows.size());
        for (OnlineOrderKaisiQuoteItem row : rows) {
            result.add(KaisiWorkbenchConvertUtils.toQuoteItemVo(row));
        }
        return result;
    }

    @Override
    public List<Map<String, Object>> queryCrawlerQueryParams(String quotationId, String storeId) {
        // 当前阶段先保留接口，返回空数组；后续按真实抓价参数表补充。
        return Collections.emptyList();
    }

    /**
     * 保证任务存在
     */
    private OnlineOrderKaisiTask ensureTask(String taskNo, Map<String, Object> payload) {
        OnlineOrderKaisiTask task = taskMapper.selectOne(
            Wrappers.<OnlineOrderKaisiTask>lambdaQuery().eq(OnlineOrderKaisiTask::getTaskNo, taskNo).last("limit 1")
        );
        if (task != null) {
            return task;
        }
        OnlineOrderKaisiTask created = KaisiIngestConvertUtils.buildInitTask(taskNo, payload, "python");
        taskMapper.insert(created);
        return created;
    }

    /**
     * 追加任务时间线日志
     */
    private void appendTaskLog(String taskNo, String event, Map<String, Object> payload) {
        taskLogMapper.insert(KaisiIngestConvertUtils.buildTaskLog(taskNo, event, payload));
    }

    /**
     * 根据事件更新任务主状态
     */
    private void updateTaskByEvent(OnlineOrderKaisiTask task, String event, Map<String, Object> payload) {
        KaisiIngestConvertUtils.applyTaskByEvent(task, event, payload);
        taskMapper.updateById(task);
    }

    /**
     * 同步报价单状态
     */
    private void syncQuotationByEvent(String taskNo, String event, Map<String, Object> payload) {
        if (StrUtil.equals(event, KaisiEventTypeConstants.TASK_ONLINE_ORDER_STATUS)) {
            String quotationId = KaisiMapUtils.getString(payload, "quotationId");
            String storeId = KaisiMapUtils.getString(payload, "storeId");
            if (StrUtil.isBlank(quotationId)) {
                return;
            }
            upsertQuotation(taskNo, payload, quotationId, storeId);
            appendExecutionLog(taskNo, payload, event, "INFO");
            return;
        }

        if (StrUtil.equals(event, KaisiEventTypeConstants.TASK_ONLINE_ORDER_SUBMIT)) {
            String quotationId = KaisiMapUtils.getString(payload, "quotationId");
            String storeId = KaisiMapUtils.getString(payload, "storeId");
            if (StrUtil.isBlank(quotationId)) {
                return;
            }
            upsertQuotation(taskNo, payload, quotationId, storeId);
            syncSubmitItems(taskNo, quotationId, storeId, KaisiMapUtils.getMapList(payload, "submitResults"));
            appendExecutionLog(taskNo, payload, event, "INFO");
        }
    }

    /**
     * 报价单主表更新
     */
    private OnlineOrderKaisiQuotation upsertQuotation(String taskNo, Map<String, Object> payload, String quotationId, String storeId) {
        OnlineOrderKaisiQuotation quotation = quotationMapper.selectOne(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .eq(OnlineOrderKaisiQuotation::getQuotationId, quotationId)
                .eq(StrUtil.isNotBlank(storeId), OnlineOrderKaisiQuotation::getStoreId, storeId)
                .last("limit 1")
        );
        if (quotation == null) {
            quotation = new OnlineOrderKaisiQuotation();
            quotation.setQuotationId(quotationId);
            quotation.setStoreId(storeId);
        }

        KaisiIngestConvertUtils.applyQuotation(quotation, payload);

        if (quotation.getId() == null) {
            quotationMapper.insert(quotation);
        } else {
            quotationMapper.updateById(quotation);
        }

        updateTaskCounter(taskNo, quotation);
        return quotation;
    }

    /**
     * 同步明细
     */
    private void syncQuotationItems(String quotationId, String storeId, List<Map<String, Object>> items) {
        if (CollUtil.isEmpty(items)) {
            return;
        }
        for (Map<String, Object> item : items) {
            String onlineOrderItemId = KaisiMapUtils.getString(item, "onlineOrderItemId");
            String resolveResultId = KaisiMapUtils.getString(item, "resolveResultId");
            OnlineOrderKaisiQuoteItem row = quoteItemMapper.selectOne(
                Wrappers.<OnlineOrderKaisiQuoteItem>lambdaQuery()
                    .eq(OnlineOrderKaisiQuoteItem::getQuotationId, quotationId)
                    .eq(OnlineOrderKaisiQuoteItem::getStoreId, storeId)
                    .eq(StrUtil.isNotBlank(onlineOrderItemId), OnlineOrderKaisiQuoteItem::getOnlineOrderItemId, onlineOrderItemId)
                    .eq(StrUtil.isBlank(onlineOrderItemId) && StrUtil.isNotBlank(resolveResultId), OnlineOrderKaisiQuoteItem::getResolveResultId, resolveResultId)
                    .last("limit 1")
            );
            if (row == null) {
                row = new OnlineOrderKaisiQuoteItem();
                row.setQuotationId(quotationId);
                row.setStoreId(storeId);
            }
            KaisiIngestConvertUtils.applyQuoteItem(row, item);
            if (row.getId() == null) {
                quoteItemMapper.insert(row);
            } else {
                quoteItemMapper.updateById(row);
            }
        }
    }

    /**
     * 同步提交结果明细
     */
    private void syncSubmitItems(String taskNo, String quotationId, String storeId, List<Map<String, Object>> submitResults) {
        if (CollUtil.isEmpty(submitResults)) {
            return;
        }
        for (Map<String, Object> submitResult : submitResults) {
            submitItemMapper.insert(KaisiIngestConvertUtils.buildSubmitItem(taskNo, quotationId, storeId, submitResult));
        }
    }

    /**
     * 执行日志落库
     */
    private void appendExecutionLog(String taskNo, Map<String, Object> payload, String eventType, String level) {
        String quotationId = KaisiMapUtils.getString(payload, "quotationId");
        if (StrUtil.isBlank(quotationId)) {
            return;
        }
        executionLogMapper.insert(KaisiIngestConvertUtils.buildExecutionLog(taskNo, eventType, level, payload));
    }

    /**
     * 根据报价单状态更新首页统计
     */
    private void updateTaskCounter(String taskNo, OnlineOrderKaisiQuotation quotation) {
        OnlineOrderKaisiTask task = taskMapper.selectOne(
            Wrappers.<OnlineOrderKaisiTask>lambdaQuery().eq(OnlineOrderKaisiTask::getTaskNo, taskNo).last("limit 1")
        );
        if (task == null) {
            return;
        }
        Integer catchCount = task.getTodayCatchCount();
        Integer priceCount = task.getTodayPriceCount();
        Integer submitCount = task.getTodaySubmitCount();
        if (StrUtil.equalsAnyIgnoreCase(quotation.getCurrentNodeCode(), "RECEIVE_QUOTATION", "RECEIVE_QUOTATION_DETAIL")) {
            catchCount = ObjectUtil.defaultIfNull(catchCount, 0) + 1;
        }
        if (StrUtil.equalsAnyIgnoreCase(quotation.getCurrentNodeCode(), "AUTO_PRICE_FILLING", "QUEUE_PRICE_FILL")) {
            priceCount = ObjectUtil.defaultIfNull(priceCount, 0) + 1;
        }
        if (StrUtil.equalsAnyIgnoreCase(quotation.getCurrentNodeCode(), "SUBMIT_QUOTATION", "COMPLETED")) {
            submitCount = ObjectUtil.defaultIfNull(submitCount, 0) + 1;
        }
        task.setTodayCatchCount(catchCount);
        task.setTodayPriceCount(priceCount);
        task.setTodaySubmitCount(submitCount);
        taskMapper.updateById(task);
    }
}
