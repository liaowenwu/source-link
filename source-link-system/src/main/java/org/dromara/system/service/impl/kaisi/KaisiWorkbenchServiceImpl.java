package org.dromara.system.service.impl.kaisi;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.date.DateUtil;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.common.satoken.utils.LoginHelper;
import org.dromara.system.domain.bo.kaisi.KaisiManualPriceSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQuotationQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiSyncTaskCreateBo;
import org.dromara.system.domain.bo.kaisi.KaisiWorkbenchSettingSaveBo;
import org.dromara.system.domain.bo.kaisi.UserPartCrawlerPlatformConfigSaveBo;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuoteItem;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuotation;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTask;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiTaskLog;
import org.dromara.system.domain.kaisi.PartCrawlerPlatform;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformBrand;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformQuality;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformRegion;
import org.dromara.system.domain.kaisi.PartCrawlerPlatformSupplier;
import org.dromara.system.domain.kaisi.UserKaisiConfig;
import org.dromara.system.domain.kaisi.UserPartCrawlerPlatformConfig;
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
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiQuoteItemMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiQuotationMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiTaskLogMapper;
import org.dromara.system.mapper.kaisi.OnlineOrderKaisiTaskMapper;
import org.dromara.system.mapper.kaisi.PartCrawlerPlatformBrandMapper;
import org.dromara.system.mapper.kaisi.PartCrawlerPlatformMapper;
import org.dromara.system.mapper.kaisi.PartCrawlerPlatformQualityMapper;
import org.dromara.system.mapper.kaisi.PartCrawlerPlatformRegionMapper;
import org.dromara.system.mapper.kaisi.PartCrawlerPlatformSupplierMapper;
import org.dromara.system.mapper.kaisi.UserKaisiConfigMapper;
import org.dromara.system.mapper.kaisi.UserPartCrawlerPlatformConfigMapper;
import org.dromara.system.service.kaisi.IKaisiIngestService;
import org.dromara.system.service.kaisi.IKaisiWorkbenchService;
import org.dromara.system.utils.kaisi.KaisiPlatformConfigConvertUtils;
import org.dromara.system.utils.kaisi.KaisiWorkbenchConvertUtils;
import org.dromara.system.utils.kaisi.KaisiWorkbenchSettingUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 开思工作台服务实现
 */
@Service
@RequiredArgsConstructor
public class KaisiWorkbenchServiceImpl implements IKaisiWorkbenchService {

    private final OnlineOrderKaisiTaskMapper taskMapper;
    private final OnlineOrderKaisiTaskLogMapper taskLogMapper;
    private final OnlineOrderKaisiQuotationMapper quotationMapper;
    private final OnlineOrderKaisiQuoteItemMapper quoteItemMapper;
    private final IKaisiIngestService kaisiIngestService;
    private final UserKaisiConfigMapper userKaisiConfigMapper;
    private final UserPartCrawlerPlatformConfigMapper userPlatformConfigMapper;
    private final PartCrawlerPlatformMapper platformMapper;
    private final PartCrawlerPlatformQualityMapper platformQualityMapper;
    private final PartCrawlerPlatformBrandMapper platformBrandMapper;
    private final PartCrawlerPlatformRegionMapper platformRegionMapper;
    private final PartCrawlerPlatformSupplierMapper platformSupplierMapper;

    @Override
    public KaisiDashboardVo getDashboard() {
        OnlineOrderKaisiTask task = taskMapper.selectOne(
            Wrappers.<OnlineOrderKaisiTask>lambdaQuery()
                .orderByDesc(OnlineOrderKaisiTask::getUpdateTime)
                .last("limit 1")
        );

        KaisiDashboardVo vo = new KaisiDashboardVo();
        if (task == null) {
            vo.setServiceStatus("INIT");
            vo.setTodayCatchCount(0);
            vo.setTodayPriceCount(0);
            vo.setTodaySubmitCount(0);
            vo.setRunningSeconds(0L);
            vo.setLatestCatchTime(StrUtil.EMPTY);
            vo.setWaitPriceCount(0);
            vo.setWaitSubmitCount(0);
            vo.setTimeline(Collections.emptyList());
            vo.setAlertTimeline(Collections.emptyList());
            vo.setQuickQuotations(Collections.emptyList());
            return vo;
        }

        vo.setTaskNo(task.getTaskNo());
        vo.setServiceStatus(task.getServiceStatus());
        vo.setCurrentMessage(task.getCurrentMessage());
        vo.setTodayCatchCount(ObjectUtil.defaultIfNull(task.getTodayCatchCount(), 0));
        vo.setTodayPriceCount(ObjectUtil.defaultIfNull(task.getTodayPriceCount(), 0));
        vo.setTodaySubmitCount(ObjectUtil.defaultIfNull(task.getTodaySubmitCount(), 0));
        vo.setLastPollTime(task.getUpdateTime() == null ? StrUtil.EMPTY : DateUtil.formatDateTime(task.getUpdateTime()));
        vo.setRunningSeconds(KaisiWorkbenchConvertUtils.calculateRunningSeconds(task));
        vo.setLatestCatchTime(queryLatestCatchTime());
        vo.setWaitPriceCount(countQuotationByFlowStatus("WAIT_PRICE_FILL", null));
        vo.setWaitSubmitCount(countQuotationByFlowStatus("WAIT_SUBMIT", null));
        vo.setTimeline(listTimeline(task.getTaskNo(), StrUtil.EMPTY, 20));
        vo.setAlertTimeline(listAlertTimeline(20));
        vo.setQuickQuotations(queryQuickQuotations());
        return vo;
    }

    @Override
    public KaisiWorkbenchSettingVo getSetting() {
        Long userId = LoginHelper.getUserId();
        UserKaisiConfig config = userKaisiConfigMapper.selectOne(
            Wrappers.<UserKaisiConfig>lambdaQuery()
                .eq(UserKaisiConfig::getUserId, userId)
                .last("limit 1")
        );
        List<UserPartCrawlerPlatformConfig> platformRows = userPlatformConfigMapper.selectList(
            Wrappers.<UserPartCrawlerPlatformConfig>lambdaQuery()
                .eq(UserPartCrawlerPlatformConfig::getUserId, userId)
                .orderByAsc(UserPartCrawlerPlatformConfig::getPlatformId)
        );
        return KaisiWorkbenchSettingUtils.buildSettingVo(userId, config, platformRows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void saveSetting(KaisiWorkbenchSettingSaveBo bo) {
        Long userId = LoginHelper.getUserId();
        UserKaisiConfig config = userKaisiConfigMapper.selectOne(
            Wrappers.<UserKaisiConfig>lambdaQuery()
                .eq(UserKaisiConfig::getUserId, userId)
                .last("limit 1")
        );
        if (config == null) {
            userKaisiConfigMapper.insert(KaisiWorkbenchSettingUtils.toUserKaisiConfig(userId, bo));
        } else {
            KaisiWorkbenchSettingUtils.applyUserKaisiConfig(config, userId, bo);
            userKaisiConfigMapper.updateById(config);
        }

        if (CollUtil.isEmpty(bo.getPlatformConfigs())) {
            return;
        }
        for (UserPartCrawlerPlatformConfigSaveBo platformBo : bo.getPlatformConfigs()) {
            PartCrawlerPlatform platform = platformMapper.selectOne(
                Wrappers.<PartCrawlerPlatform>lambdaQuery()
                    .eq(PartCrawlerPlatform::getPlatformCode, StrUtil.trim(platformBo.getPlatformCode()))
                    .last("limit 1")
            );
            if (platform == null) {
                continue;
            }
            UserPartCrawlerPlatformConfig row = userPlatformConfigMapper.selectOne(
                Wrappers.<UserPartCrawlerPlatformConfig>lambdaQuery()
                    .eq(UserPartCrawlerPlatformConfig::getUserId, userId)
                    .eq(UserPartCrawlerPlatformConfig::getPlatformCode, platform.getPlatformCode())
                    .last("limit 1")
            );
            if (row == null) {
                userPlatformConfigMapper.insert(KaisiWorkbenchSettingUtils.toUserPlatformConfig(userId, platform, platformBo));
            } else {
                KaisiWorkbenchSettingUtils.applyUserPlatformConfig(row, userId, platform, platformBo);
                userPlatformConfigMapper.updateById(row);
            }
        }
    }

    @Override
    public List<PartCrawlerPlatformQualityVo> listSettingQualities(Long platformId) {
        List<PartCrawlerPlatformQuality> rows = platformQualityMapper.selectList(
            Wrappers.<PartCrawlerPlatformQuality>lambdaQuery()
                .eq(PartCrawlerPlatformQuality::getPlatformId, platformId)
                .eq(PartCrawlerPlatformQuality::getStatus, 1)
                .orderByAsc(PartCrawlerPlatformQuality::getOrderNum)
                .orderByAsc(PartCrawlerPlatformQuality::getId)
        );
        return KaisiPlatformConfigConvertUtils.toPlatformQualityVoList(rows);
    }

    @Override
    public TableDataInfo<PartCrawlerPlatformBrandVo> listSettingBrands(Long platformId, String qualityOriginIds, String brandName, PageQuery pageQuery) {
        Page<PartCrawlerPlatformBrand> page = platformBrandMapper.selectSettingBrands(
            pageQuery.build(),
            platformId,
            KaisiWorkbenchSettingUtils.parseStringList(qualityOriginIds),
            StrUtil.trim(brandName)
        );
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformBrandVoList(page.getRecords()));
    }

    @Override
    public List<PartCrawlerPlatformRegionVo> listSettingRegions(Long platformId) {
        List<PartCrawlerPlatformRegion> rows = platformRegionMapper.selectList(
            Wrappers.<PartCrawlerPlatformRegion>lambdaQuery()
                .eq(PartCrawlerPlatformRegion::getPlatformId, platformId)
                .eq(PartCrawlerPlatformRegion::getStatus, 1)
                .orderByAsc(PartCrawlerPlatformRegion::getId)
        );
        return KaisiPlatformConfigConvertUtils.toPlatformRegionVoList(rows);
    }

    @Override
    public TableDataInfo<PartCrawlerPlatformSupplierVo> listSettingSuppliers(Long platformId, String supplierName, PageQuery pageQuery) {
        List<String> keywords = KaisiWorkbenchSettingUtils.parseSearchKeywords(supplierName);
        LambdaQueryWrapper<PartCrawlerPlatformSupplier> lqw = Wrappers.lambdaQuery();
        lqw.eq(PartCrawlerPlatformSupplier::getPlatformId, platformId)
            .eq(PartCrawlerPlatformSupplier::getStatus, 1)
            .orderByAsc(PartCrawlerPlatformSupplier::getId);
        if (CollUtil.isNotEmpty(keywords)) {
            lqw.and(wrapper -> {
                for (int index = 0; index < keywords.size(); index++) {
                    if (index == 0) {
                        wrapper.like(PartCrawlerPlatformSupplier::getSupplierName, keywords.get(index));
                    } else {
                        wrapper.or().like(PartCrawlerPlatformSupplier::getSupplierName, keywords.get(index));
                    }
                }
            });
        }
        Page<PartCrawlerPlatformSupplier> page = platformSupplierMapper.selectPage(pageQuery.build(), lqw);
        return KaisiPlatformConfigConvertUtils.buildTable(page, KaisiPlatformConfigConvertUtils.toPlatformSupplierVoList(page.getRecords()));
    }

    @Override
    public List<KaisiTimelineVo> listTimeline(String taskNo, String eventType, Integer limit) {
        int maxCount = ObjectUtil.defaultIfNull(limit, 20);
        LambdaQueryWrapper<OnlineOrderKaisiTaskLog> lqw = Wrappers.lambdaQuery();
        lqw.eq(StrUtil.isNotBlank(taskNo), OnlineOrderKaisiTaskLog::getTaskNo, taskNo)
            .eq(StrUtil.isNotBlank(eventType), OnlineOrderKaisiTaskLog::getEventType, eventType)
            .orderByDesc(OnlineOrderKaisiTaskLog::getCreateTime)
            .last("limit " + Math.min(Math.max(maxCount, 1), 200));
        List<OnlineOrderKaisiTaskLog> rows = taskLogMapper.selectList(lqw);
        if (CollUtil.isEmpty(rows)) {
            return Collections.emptyList();
        }
        List<KaisiTimelineVo> result = new ArrayList<>(rows.size());
        for (OnlineOrderKaisiTaskLog row : rows) {
            result.add(KaisiWorkbenchConvertUtils.toTimelineVo(row));
        }
        return result;
    }

    @Override
    public TableDataInfo<KaisiQuotationVo> listQuotations(KaisiQuotationQueryBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<OnlineOrderKaisiQuotation> lqw = Wrappers.lambdaQuery();
        lqw.like(StrUtil.isNotBlank(bo.getQuotationId()), OnlineOrderKaisiQuotation::getQuotationId, bo.getQuotationId())
            .like(StrUtil.isNotBlank(bo.getInquiryId()), OnlineOrderKaisiQuotation::getInquiryId, bo.getInquiryId())
            .eq(StrUtil.isNotBlank(bo.getStoreId()), OnlineOrderKaisiQuotation::getStoreId, bo.getStoreId())
            .eq(StrUtil.isNotBlank(bo.getFlowStatus()), OnlineOrderKaisiQuotation::getFlowStatus, bo.getFlowStatus())
            .eq(StrUtil.isNotBlank(bo.getProcessStatus()), OnlineOrderKaisiQuotation::getProcessStatus, bo.getProcessStatus())
            .eq(ObjectUtil.isNotNull(bo.getManualPriceFillEnabled()), OnlineOrderKaisiQuotation::getManualPriceFillEnabled, bo.getManualPriceFillEnabled())
            .eq(ObjectUtil.isNotNull(bo.getNeedAlert()), OnlineOrderKaisiQuotation::getNeedAlert, bo.getNeedAlert())
            .eq(ObjectUtil.isNotNull(bo.getAssignedUserId()), OnlineOrderKaisiQuotation::getAssignedUserId, bo.getAssignedUserId())
            .orderByDesc(OnlineOrderKaisiQuotation::getLastLogTime);

        String scene = StrUtil.blankToDefault(bo.getScene(), StrUtil.EMPTY).toUpperCase();
        if (StrUtil.equals(scene, "TODAY") || StrUtil.equals(scene, "MANUAL")) {
            Date begin = DateUtil.beginOfDay(new Date());
            Date end = DateUtil.endOfDay(new Date());
            lqw.ge(OnlineOrderKaisiQuotation::getLastLogTime, begin)
                .le(OnlineOrderKaisiQuotation::getLastLogTime, end);
        }
        if (StrUtil.equals(scene, "MANUAL")) {
            lqw.eq(OnlineOrderKaisiQuotation::getFlowStatus, "WAIT_PRICE_FILL")
                .eq(OnlineOrderKaisiQuotation::getManualPriceFillEnabled, true);
        }
        if (StrUtil.isNotBlank(bo.getBeginTime())) {
            lqw.ge(OnlineOrderKaisiQuotation::getLastLogTime, DateUtil.parseDateTime(bo.getBeginTime()));
        }
        if (StrUtil.isNotBlank(bo.getEndTime())) {
            lqw.le(OnlineOrderKaisiQuotation::getLastLogTime, DateUtil.parseDateTime(bo.getEndTime()));
        }

        Page<OnlineOrderKaisiQuotation> page = quotationMapper.selectPage(pageQuery.build(), lqw);
        List<KaisiQuotationVo> records = new ArrayList<>();
        for (OnlineOrderKaisiQuotation row : page.getRecords()) {
            records.add(KaisiWorkbenchConvertUtils.toQuotationVo(row));
        }
        Page<KaisiQuotationVo> voPage = new Page<>(page.getCurrent(), page.getSize(), page.getTotal());
        voPage.setRecords(records);
        return TableDataInfo.build(voPage);
    }

    @Override
    public List<KaisiQuoteItemVo> listQuotationItems(String quotationId, String storeId) {
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
    @Transactional(rollbackFor = Exception.class)
    public void saveManualPrice(KaisiManualPriceSaveBo bo) {
        OnlineOrderKaisiQuoteItem item = quoteItemMapper.selectById(bo.getItemId());
        if (item == null) {
            return;
        }
        item.setFinalPrice(bo.getFinalPrice());
        item.setUnmatchedReason(bo.getUnmatchedReason());
        item.setRemark(bo.getRemark());
        item.setItemProcessStatus(StrUtil.isBlank(bo.getUnmatchedReason()) ? "PRICED" : "UNMATCHED");
        quoteItemMapper.updateById(item);

        OnlineOrderKaisiQuotation quotation = quotationMapper.selectOne(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .eq(OnlineOrderKaisiQuotation::getQuotationId, item.getQuotationId())
                .eq(OnlineOrderKaisiQuotation::getStoreId, item.getStoreId())
                .last("limit 1")
        );
        if (quotation != null) {
            KaisiWorkbenchConvertUtils.applyManualPriceSavedStatus(quotation);
            quotationMapper.updateById(quotation);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void submitQuotation(String quotationId, String storeId) {
        OnlineOrderKaisiQuotation quotation = quotationMapper.selectOne(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .eq(OnlineOrderKaisiQuotation::getQuotationId, quotationId)
                .eq(StrUtil.isNotBlank(storeId), OnlineOrderKaisiQuotation::getStoreId, storeId)
                .last("limit 1")
        );
        if (quotation == null) {
            return;
        }
        KaisiWorkbenchConvertUtils.applySubmitQueuedStatus(quotation);
        quotationMapper.updateById(quotation);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void retryQuotation(String quotationId, String storeId) {
        OnlineOrderKaisiQuotation quotation = quotationMapper.selectOne(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .eq(OnlineOrderKaisiQuotation::getQuotationId, quotationId)
                .eq(StrUtil.isNotBlank(storeId), OnlineOrderKaisiQuotation::getStoreId, storeId)
                .last("limit 1")
        );
        if (quotation == null) {
            return;
        }
        KaisiWorkbenchConvertUtils.applyRetryStatus(quotation);
        quotationMapper.updateById(quotation);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String startTask() {
        KaisiSyncTaskCreateBo bo = new KaisiSyncTaskCreateBo();
        bo.setTaskType("batch");
        bo.setBizType("KAISI_ONLINE_ORDER");
        bo.setTriggerBy("workbench-start");
        bo.setTotalCount(1);
        String taskNo = kaisiIngestService.createSyncTaskNo(bo);

        OnlineOrderKaisiTask task = taskMapper.selectOne(
            Wrappers.<OnlineOrderKaisiTask>lambdaQuery().eq(OnlineOrderKaisiTask::getTaskNo, taskNo).last("limit 1")
        );
        if (task != null) {
            task.setServiceStatus("RUNNING");
            task.setStartedAt(new Date());
            task.setStoppedAt(null);
            task.setCurrentMessage("工作台手动开启任务");
            taskMapper.updateById(task);
            appendTaskControlLog(taskNo, "TASK_START", "工作台手动开启任务", "INFO");
        }
        return taskNo;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void stopTask() {
        OnlineOrderKaisiTask task = taskMapper.selectOne(
            Wrappers.<OnlineOrderKaisiTask>lambdaQuery()
                .in(OnlineOrderKaisiTask::getServiceStatus, "RUNNING", "STARTING", "STOPPING")
                .orderByDesc(OnlineOrderKaisiTask::getUpdateTime)
                .last("limit 1")
        );
        if (task == null) {
            return;
        }
        task.setServiceStatus("STOPPED");
        task.setStoppedAt(new Date());
        task.setCurrentMessage("工作台手动停止任务");
        taskMapper.updateById(task);
        appendTaskControlLog(task.getTaskNo(), "TASK_CONTROL", "工作台手动停止任务", "WARNING");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String runOnceTask() {
        KaisiSyncTaskCreateBo bo = new KaisiSyncTaskCreateBo();
        bo.setTaskType("single");
        bo.setBizType("KAISI_ONLINE_ORDER");
        bo.setTriggerBy("workbench-run-once");
        bo.setTotalCount(1);
        String taskNo = kaisiIngestService.createSyncTaskNo(bo);
        OnlineOrderKaisiTask task = taskMapper.selectOne(
            Wrappers.<OnlineOrderKaisiTask>lambdaQuery().eq(OnlineOrderKaisiTask::getTaskNo, taskNo).last("limit 1")
        );
        if (task != null) {
            task.setServiceStatus("STARTING");
            task.setStartedAt(new Date());
            task.setStoppedAt(null);
            task.setCurrentMessage("已触发执行一次");
            taskMapper.updateById(task);
            appendTaskControlLog(taskNo, "TASK_ONCE", "工作台触发执行一次", "INFO");
        }
        return taskNo;
    }

    @Override
    public List<KaisiHistoryPartVo> listHistoryParts(String beginTime, String endTime, String quotationId, String partsKeyword) {
        return quoteItemMapper.selectHistoryPartStats(beginTime, endTime, quotationId, partsKeyword);
    }

    @Override
    public List<KaisiPriceTrendPointVo> listPriceTrend(String beginTime, String endTime, String quotationId, String partsNum, String brandName, String partsBrandQuality) {
        if (StrUtil.isBlank(partsNum)) {
            return Collections.emptyList();
        }
        return quoteItemMapper.selectPriceTrend(beginTime, endTime, quotationId, partsNum, brandName, partsBrandQuality);
    }

    /**
     * 首页快捷报价单
     */
    private List<KaisiQuotationVo> queryQuickQuotations() {
        List<OnlineOrderKaisiQuotation> rows = quotationMapper.selectList(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .orderByDesc(OnlineOrderKaisiQuotation::getLastLogTime)
                .last("limit 20")
        );
        if (CollUtil.isEmpty(rows)) {
            return Collections.emptyList();
        }
        List<KaisiQuotationVo> result = new ArrayList<>(rows.size());
        for (OnlineOrderKaisiQuotation row : rows) {
            result.add(KaisiWorkbenchConvertUtils.toQuotationVo(row));
        }
        return result;
    }

    /**
     * 异常提醒时间线
     */
    private List<KaisiTimelineVo> listAlertTimeline(Integer limit) {
        int maxCount = ObjectUtil.defaultIfNull(limit, 20);
        List<OnlineOrderKaisiQuotation> rows = quotationMapper.selectList(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .eq(OnlineOrderKaisiQuotation::getNeedAlert, true)
                .orderByDesc(OnlineOrderKaisiQuotation::getLastLogTime)
                .last("limit " + Math.min(Math.max(maxCount, 1), 200))
        );
        if (CollUtil.isEmpty(rows)) {
            return Collections.emptyList();
        }
        List<KaisiTimelineVo> result = new ArrayList<>(rows.size());
        for (OnlineOrderKaisiQuotation row : rows) {
            KaisiTimelineVo vo = new KaisiTimelineVo();
            vo.setTaskNo(StrUtil.blankToDefault(row.getQuotationId(), "-"));
            vo.setEventType("ALERT");
            vo.setEventLevel("WARNING");
            vo.setDisplayTitle(StrUtil.blankToDefault(row.getQuotationId(), "异常报价单"));
            vo.setDisplayContent(StrUtil.blankToDefault(row.getErrorMessage(),
                StrUtil.format("{} 补价完成仍存在未匹配的价格，待人工处理", row.getQuotationId())));
            vo.setQuotationId(row.getQuotationId());
            vo.setStoreId(row.getStoreId());
            vo.setCreateTime(row.getLastLogTime());
            result.add(vo);
        }
        return result;
    }

    /**
     * 统计指定流程状态报价单数量
     */
    private Integer countQuotationByFlowStatus(String flowStatus, Boolean manualPriceFillEnabled) {
        LambdaQueryWrapper<OnlineOrderKaisiQuotation> lqw = Wrappers.lambdaQuery();
        lqw.eq(OnlineOrderKaisiQuotation::getFlowStatus, flowStatus)
            .eq(ObjectUtil.isNotNull(manualPriceFillEnabled), OnlineOrderKaisiQuotation::getManualPriceFillEnabled, manualPriceFillEnabled)
            .ge(OnlineOrderKaisiQuotation::getLastLogTime, DateUtil.beginOfDay(new Date()))
            .le(OnlineOrderKaisiQuotation::getLastLogTime, DateUtil.endOfDay(new Date()));
        Long count = quotationMapper.selectCount(lqw);
        return count == null ? 0 : count.intValue();
    }

    /**
     * 最近抓取时间
     */
    private String queryLatestCatchTime() {
        OnlineOrderKaisiQuotation quotation = quotationMapper.selectOne(
            Wrappers.<OnlineOrderKaisiQuotation>lambdaQuery()
                .orderByDesc(OnlineOrderKaisiQuotation::getLastLogTime)
                .last("limit 1")
        );
        if (quotation == null || quotation.getLastLogTime() == null) {
            return StrUtil.EMPTY;
        }
        return DateUtil.formatDateTime(quotation.getLastLogTime());
    }

    /**
     * 记录任务控制日志
     */
    private void appendTaskControlLog(String taskNo, String eventType, String message, String level) {
        OnlineOrderKaisiTaskLog row = new OnlineOrderKaisiTaskLog();
        row.setTaskNo(taskNo);
        row.setEventCode(eventType);
        row.setEventType(eventType);
        row.setEventLevel(level);
        row.setDisplayTitle(eventType);
        row.setDisplayContent(message);
        Map<String, Object> payload = new HashMap<>(4);
        payload.put("eventType", eventType);
        payload.put("message", message);
        payload.put("operator", "workbench");
        row.setRawPayload(cn.hutool.json.JSONUtil.toJsonStr(payload));
        taskLogMapper.insert(row);
    }
}
