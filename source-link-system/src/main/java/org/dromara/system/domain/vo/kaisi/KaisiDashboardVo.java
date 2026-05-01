package org.dromara.system.domain.vo.kaisi;

import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;

/**
 * 开思首页聚合视图
 */
@Data
public class KaisiDashboardVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private String taskNo;

    private String serviceStatus;

    private String currentMessage;

    private Integer todayCatchCount;

    private Integer todayPriceCount;

    private Integer todaySubmitCount;

    private Long runningSeconds;

    private String lastPollTime;

    /**
     * 最近抓取时间
     */
    private String latestCatchTime;

    /**
     * 待补价数量
     */
    private Integer waitPriceCount;

    /**
     * 待提交数量
     */
    private Integer waitSubmitCount;

    private List<KaisiTimelineVo> timeline;

    /**
     * 异常提醒时间线
     */
    private List<KaisiTimelineVo> alertTimeline;

    private List<KaisiQuotationVo> quickQuotations;
}
