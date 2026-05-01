package org.dromara.system.utils.kaisi;

import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiExecutionLog;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuotation;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuoteItem;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiSubmitItem;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTask;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTaskLog;

import java.util.Date;
import java.util.Map;

/**
 * 开思 ingest 对象转换工具
 */
public class KaisiIngestConvertUtils {

    private KaisiIngestConvertUtils() {
    }

    public static OnlineOrderKaisiTask buildInitTask(String taskNo, Map<String, Object> payload, String defaultTriggerBy) {
        OnlineOrderKaisiTask task = new OnlineOrderKaisiTask();
        task.setTaskNo(taskNo);
        task.setTaskType(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "taskType"), "single"));
        task.setBizType(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "bizType"), "KAISI_ONLINE_ORDER"));
        task.setTriggerBy(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "triggerBy"), defaultTriggerBy));
        task.setTotalCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "totalCount", 1), 1));
        task.setServiceStatus("INIT");
        task.setSuccessCount(0);
        task.setFailCount(0);
        task.setTodayCatchCount(0);
        task.setTodayPriceCount(0);
        task.setTodaySubmitCount(0);
        return task;
    }

    public static OnlineOrderKaisiTaskLog buildTaskLog(String taskNo, String event, Map<String, Object> payload) {
        OnlineOrderKaisiTaskLog log = new OnlineOrderKaisiTaskLog();
        log.setTaskNo(taskNo);
        log.setEventCode(event);
        log.setEventType(event);
        log.setEventLevel(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "level"), "INFO"));
        log.setDisplayTitle(event);
        log.setDisplayContent(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "message"), event));
        log.setQuotationId(KaisiMapUtils.getString(payload, "quotationId"));
        log.setStoreId(KaisiMapUtils.getString(payload, "storeId"));
        log.setRawPayload(JSONUtil.toJsonStr(payload));
        return log;
    }

    public static void applyTaskByEvent(OnlineOrderKaisiTask task, String event, Map<String, Object> payload) {
        task.setCurrentMessage(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "message"), task.getCurrentMessage()));
        task.setCurrentNodeCode(KaisiMapUtils.getString(payload, "currentNodeCode"));
        task.setCurrentNodeName(KaisiMapUtils.getString(payload, "currentNodeName"));
        task.setSuccessCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "successCount", task.getSuccessCount()), task.getSuccessCount()));
        task.setFailCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "failCount", task.getFailCount()), task.getFailCount()));
        task.setTotalCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "totalCount", task.getTotalCount()), task.getTotalCount()));

        if (StrUtil.equals(event, KaisiEventTypeConstants.TASK_START)) {
            task.setServiceStatus("RUNNING");
            if (task.getStartedAt() == null) {
                task.setStartedAt(new Date());
            }
        } else if (StrUtil.equalsAny(event, KaisiEventTypeConstants.TASK_DONE, KaisiEventTypeConstants.TASK_RESULT)) {
            task.setServiceStatus("STOPPED");
            task.setStoppedAt(new Date());
        } else if (StrUtil.equals(event, KaisiEventTypeConstants.TASK_ERROR)) {
            task.setServiceStatus("ERROR");
            task.setErrorMessage(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "error"), KaisiMapUtils.getString(payload, "message")));
        } else if (StrUtil.equals(event, KaisiEventTypeConstants.TASK_CONTROL)) {
            String action = KaisiMapUtils.getString(payload, "action");
            if (StrUtil.equalsIgnoreCase(action, "TERMINATE")) {
                task.setServiceStatus("STOPPING");
            }
        }
    }

    public static void applyQuotation(OnlineOrderKaisiQuotation quotation, Map<String, Object> payload) {
        quotation.setInquiryId(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "inquiryId"), quotation.getInquiryId()));
        quotation.setSupplierCompanyId(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "supplierCompanyId"), quotation.getSupplierCompanyId()));
        quotation.setStatusId(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "statusId"), quotation.getStatusId()));
        quotation.setStatusIdDesc(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "statusIdDesc"), quotation.getStatusIdDesc()));
        quotation.setFlowStatus(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "flowStatus"), quotation.getFlowStatus()));
        quotation.setProcessStatus(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "processStatus"), quotation.getProcessStatus()));
        quotation.setCurrentNodeCode(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "currentNodeCode"), quotation.getCurrentNodeCode()));
        quotation.setCurrentNodeName(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "currentNodeName"), quotation.getCurrentNodeName()));
        quotation.setManualPriceFillEnabled(ObjectUtil.defaultIfNull(KaisiMapUtils.getBoolean(payload, "manualPriceFillEnabled", quotation.getManualPriceFillEnabled()), false));
        quotation.setAutoSubmitEnabled(ObjectUtil.defaultIfNull(KaisiMapUtils.getBoolean(payload, "autoSubmitEnabled", quotation.getAutoSubmitEnabled()), false));
        quotation.setItemCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "itemCount", quotation.getItemCount()), 0));
        quotation.setQuotedItemCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "quotedItemCount", quotation.getQuotedItemCount()), 0));
        quotation.setUnquoteItemCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "unquoteItemCount", quotation.getUnquoteItemCount()), 0));
        quotation.setSubmittedItemCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "submittedItemCount", quotation.getSubmittedItemCount()), 0));
        quotation.setExceptionItemCount(ObjectUtil.defaultIfNull(KaisiMapUtils.getInteger(payload, "exceptionItemCount", quotation.getExceptionItemCount()), 0));
        quotation.setNeedAlert(StrUtil.equalsAnyIgnoreCase(quotation.getProcessStatus(), "FAILED", "PARTIAL_EXCEPTION"));
        quotation.setNeedManualHandle(StrUtil.equalsAnyIgnoreCase(quotation.getFlowStatus(), "WAIT_PRICE_FILL", "WAIT_SUBMIT"));
        quotation.setLastMessage(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "message"), quotation.getLastMessage()));
        quotation.setErrorMessage(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "errorMessage"), quotation.getErrorMessage()));
        quotation.setRawPayload(JSONUtil.toJsonStr(payload));
        quotation.setLastLogTime(new Date());
    }

    public static OnlineOrderKaisiExecutionLog buildExecutionLog(String taskNo, String eventType, String level, Map<String, Object> payload) {
        OnlineOrderKaisiExecutionLog log = new OnlineOrderKaisiExecutionLog();
        log.setTaskNo(taskNo);
        log.setQuotationId(KaisiMapUtils.getString(payload, "quotationId"));
        log.setStoreId(KaisiMapUtils.getString(payload, "storeId"));
        log.setFlowStatus(KaisiMapUtils.getString(payload, "flowStatus"));
        log.setProcessStatus(KaisiMapUtils.getString(payload, "processStatus"));
        log.setCurrentNodeCode(KaisiMapUtils.getString(payload, "currentNodeCode"));
        log.setCurrentNodeName(KaisiMapUtils.getString(payload, "currentNodeName"));
        log.setEventType(eventType);
        log.setLogLevel(level);
        log.setMessage(StrUtil.blankToDefault(KaisiMapUtils.getString(payload, "message"), eventType));
        log.setRawPayload(JSONUtil.toJsonStr(payload));
        return log;
    }

    public static void applyQuoteItem(OnlineOrderKaisiQuoteItem row, Map<String, Object> payload) {
        row.setOnlineOrderItemId(KaisiMapUtils.getString(payload, "onlineOrderItemId"));
        row.setResolveResultId(KaisiMapUtils.getString(payload, "resolveResultId"));
        row.setPartsNum(KaisiMapUtils.getString(payload, "partsNum"));
        row.setPartsName(KaisiMapUtils.getString(payload, "partsName"));
        row.setBrandName(KaisiMapUtils.getString(payload, "brandName"));
        row.setPartsBrandQuality(KaisiMapUtils.getString(payload, "partsBrandQuality"));
        row.setStoreServiceArea(KaisiMapUtils.getString(payload, "storeServiceArea"));
        row.setQuantity(KaisiMapUtils.getInteger(payload, "quantity", 0));
        row.setSuggestedPrice(KaisiMapUtils.getBigDecimal(payload, "suggestedPrice"));
        row.setFinalPrice(KaisiMapUtils.getBigDecimal(payload, "finalPrice"));
        row.setItemProcessStatus(KaisiMapUtils.getString(payload, "itemProcessStatus"));
        row.setUnmatchedReason(KaisiMapUtils.getString(payload, "unmatchedReason"));
        row.setRemark(KaisiMapUtils.getString(payload, "remark"));
        row.setRawPayload(JSONUtil.toJsonStr(payload));
    }

    public static OnlineOrderKaisiSubmitItem buildSubmitItem(String taskNo, String quotationId, String storeId, Map<String, Object> payload) {
        OnlineOrderKaisiSubmitItem row = new OnlineOrderKaisiSubmitItem();
        row.setTaskNo(taskNo);
        row.setQuotationId(quotationId);
        row.setStoreId(storeId);
        row.setResolveResultId(KaisiMapUtils.getString(payload, "resolveResultId"));
        row.setPartsNum(KaisiMapUtils.getString(payload, "partsNum"));
        row.setPartsName(KaisiMapUtils.getString(payload, "partsName"));
        row.setSubmitStatus(KaisiMapUtils.getString(payload, "submitStatus"));
        row.setSubmitRequest(JSONUtil.toJsonStr(KaisiMapUtils.getMap(payload, "submitRequest")));
        row.setSubmitResponse(JSONUtil.toJsonStr(KaisiMapUtils.getMap(payload, "submitResponse")));
        row.setErrorMessage(KaisiMapUtils.getString(payload, "errorMessage"));
        row.setSubmittedAt(new Date());
        return row;
    }
}
