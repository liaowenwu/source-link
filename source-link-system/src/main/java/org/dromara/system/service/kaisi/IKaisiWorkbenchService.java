package org.dromara.system.service.kaisi;

import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.system.domain.bo.kaisi.KaisiManualPriceSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQuotationQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiWorkbenchSettingSaveBo;
import org.dromara.system.domain.vo.kaisi.KaisiDashboardVo;
import org.dromara.system.domain.vo.kaisi.KaisiHistoryPartVo;
import org.dromara.system.domain.vo.kaisi.KaisiWorkbenchSettingVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformBrandVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformQualityVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformRegionVo;
import org.dromara.system.domain.vo.kaisi.PartCrawlerPlatformSupplierVo;
import org.dromara.system.domain.vo.kaisi.KaisiPriceTrendPointVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuoteItemVo;
import org.dromara.system.domain.vo.kaisi.KaisiQuotationVo;
import org.dromara.system.domain.vo.kaisi.KaisiTimelineVo;

import java.util.List;

/**
 * 开思工作台业务服务
 */
public interface IKaisiWorkbenchService {

    KaisiDashboardVo getDashboard();

    /**
     * 查询当前用户工作台设置
     */
    KaisiWorkbenchSettingVo getSetting();

    /**
     * 保存当前用户工作台设置
     */
    void saveSetting(KaisiWorkbenchSettingSaveBo bo);

    /**
     * 查询平台质量选项
     */
    List<PartCrawlerPlatformQualityVo> listSettingQualities(Long platformId);

    /**
     * 按已勾选质量查询品牌选项
     */
    TableDataInfo<PartCrawlerPlatformBrandVo> listSettingBrands(Long platformId, String qualityOriginIds, String brandName, PageQuery pageQuery);

    /**
     * 查询平台区域选项
     */
    List<PartCrawlerPlatformRegionVo> listSettingRegions(Long platformId);

    /**
     * 查询平台供应商选项
     */
    TableDataInfo<PartCrawlerPlatformSupplierVo> listSettingSuppliers(Long platformId, String supplierName, PageQuery pageQuery);

    List<KaisiTimelineVo> listTimeline(String taskNo, String eventType, Integer limit);

    TableDataInfo<KaisiQuotationVo> listQuotations(KaisiQuotationQueryBo bo, PageQuery pageQuery);

    List<KaisiQuoteItemVo> listQuotationItems(String quotationId, String storeId);

    void saveManualPrice(KaisiManualPriceSaveBo bo);

    void submitQuotation(String quotationId, String storeId);

    void retryQuotation(String quotationId, String storeId);

    /**
     * 开启持续任务
     */
    String startTask();

    /**
     * 停止当前任务
     */
    void stopTask();

    /**
     * 执行一次任务
     */
    String runOnceTask();

    /**
     * 历史零件统计
     */
    List<KaisiHistoryPartVo> listHistoryParts(String beginTime, String endTime, String quotationId, String partsKeyword);

    /**
     * 价格走势
     */
    List<KaisiPriceTrendPointVo> listPriceTrend(String beginTime, String endTime, String quotationId, String partsNum, String brandName, String partsBrandQuality);
}
