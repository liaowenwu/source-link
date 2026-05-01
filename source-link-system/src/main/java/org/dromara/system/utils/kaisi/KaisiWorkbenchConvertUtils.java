package org.dromara.system.utils.kaisi;

import cn.hutool.core.util.StrUtil;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuoteItem;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuotation;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTask;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTaskLog;
import org.dromara.system.domain.vo.kaisi.KaisiQuoteItemVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuotationVo;
import org.dromara.system.domain.vo.kaisi.KaisiTimelineVo;

import java.util.Date;

/**
 * 开思工作台对象转换工具
 */
public class KaisiWorkbenchConvertUtils {

    private KaisiWorkbenchConvertUtils() {
    }

    public static KaisiQuotationVo toQuotationVo(OnlineOrderKaisiQuotation row) {
        KaisiQuotationVo vo = new KaisiQuotationVo();
        vo.setQuotationId(row.getQuotationId());
        vo.setInquiryId(row.getInquiryId());
        vo.setStoreId(row.getStoreId());
        vo.setStatusIdDesc(row.getStatusIdDesc());
        vo.setFlowStatus(row.getFlowStatus());
        vo.setProcessStatus(row.getProcessStatus());
        vo.setCurrentNodeCode(row.getCurrentNodeCode());
        vo.setCurrentNodeName(row.getCurrentNodeName());
        vo.setItemCount(row.getItemCount());
        vo.setQuotedItemCount(row.getQuotedItemCount());
        vo.setUnquoteItemCount(row.getUnquoteItemCount());
        vo.setSubmittedItemCount(row.getSubmittedItemCount());
        vo.setExceptionItemCount(row.getExceptionItemCount());
        vo.setManualPriceFillEnabled(row.getManualPriceFillEnabled());
        vo.setAutoSubmitEnabled(row.getAutoSubmitEnabled());
        vo.setNeedAlert(row.getNeedAlert());
        vo.setAssignedUserId(row.getAssignedUserId());
        vo.setLastMessage(row.getLastMessage());
        vo.setErrorMessage(row.getErrorMessage());
        vo.setLastLogTime(row.getLastLogTime());
        return vo;
    }

    public static KaisiQuoteItemVo toQuoteItemVo(OnlineOrderKaisiQuoteItem row) {
        KaisiQuoteItemVo vo = new KaisiQuoteItemVo();
        vo.setId(row.getId());
        vo.setQuotationId(row.getQuotationId());
        vo.setStoreId(row.getStoreId());
        vo.setOnlineOrderItemId(row.getOnlineOrderItemId());
        vo.setResolveResultId(row.getResolveResultId());
        vo.setPartsNum(row.getPartsNum());
        vo.setPartsName(row.getPartsName());
        vo.setBrandName(row.getBrandName());
        vo.setPartsBrandQuality(row.getPartsBrandQuality());
        vo.setStoreServiceArea(row.getStoreServiceArea());
        vo.setQuantity(row.getQuantity());
        vo.setSuggestedPrice(row.getSuggestedPrice());
        vo.setFinalPrice(row.getFinalPrice());
        vo.setItemProcessStatus(row.getItemProcessStatus());
        vo.setUnmatchedReason(row.getUnmatchedReason());
        vo.setRemark(row.getRemark());
        return vo;
    }

    public static KaisiTimelineVo toTimelineVo(OnlineOrderKaisiTaskLog row) {
        KaisiTimelineVo vo = new KaisiTimelineVo();
        vo.setTaskNo(row.getTaskNo());
        vo.setEventType(row.getEventType());
        vo.setEventLevel(row.getEventLevel());
        vo.setDisplayTitle(row.getDisplayTitle());
        vo.setDisplayContent(row.getDisplayContent());
        vo.setQuotationId(row.getQuotationId());
        vo.setStoreId(row.getStoreId());
        vo.setCreateTime(row.getCreateTime());
        return vo;
    }

    public static void applyManualPriceSavedStatus(OnlineOrderKaisiQuotation quotation) {
        quotation.setFlowStatus("WAIT_SUBMIT");
        quotation.setProcessStatus("PROCESSING");
        quotation.setCurrentNodeCode("WAIT_SUBMIT");
        quotation.setCurrentNodeName("等待提交");
        quotation.setLastMessage("人工补价已保存");
        quotation.setLastLogTime(new Date());
    }

    public static void applySubmitQueuedStatus(OnlineOrderKaisiQuotation quotation) {
        quotation.setFlowStatus("WAIT_SUBMIT");
        quotation.setProcessStatus("PROCESSING");
        quotation.setCurrentNodeCode("QUEUE_SUBMIT");
        quotation.setCurrentNodeName("进入提交队列");
        quotation.setLastMessage("已触发手动提交");
        quotation.setLastLogTime(new Date());
    }

    public static void applyRetryStatus(OnlineOrderKaisiQuotation quotation) {
        quotation.setProcessStatus("PROCESSING");
        quotation.setNeedAlert(false);
        quotation.setErrorMessage(StrUtil.EMPTY);
        quotation.setLastMessage("已触发重试");
        quotation.setLastLogTime(new Date());
    }

    public static Long calculateRunningSeconds(OnlineOrderKaisiTask task) {
        if (task.getStartedAt() == null) {
            return 0L;
        }
        Date end = task.getStoppedAt();
        if (end == null && StrUtil.equalsAnyIgnoreCase(task.getServiceStatus(), "RUNNING", "STOPPING")) {
            end = new Date();
        }
        if (end == null) {
            end = task.getStartedAt();
        }
        return Math.max(0L, (end.getTime() - task.getStartedAt().getTime()) / 1000L);
    }
}

