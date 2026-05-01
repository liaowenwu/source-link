package org.dromara.system.service.kaisi;

import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.mybatis.core.page.TableDataInfo;
import org.dromara.system.domain.bo.kaisi.KaisiBrandQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiBrandSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityBrandLinkSaveBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualityQueryBo;
import org.dromara.system.domain.bo.kaisi.KaisiQualitySaveBo;
import org.dromara.system.domain.vo.kaisi.KaisiBrandVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityBrandLinkVo;
import org.dromara.system.domain.vo.kaisi.KaisiQualityVo;

import java.util.List;

/**
 * 开思基础配置服务
 */
public interface IKaisiBaseConfigService {

    TableDataInfo<KaisiBrandVo> listBrands(KaisiBrandQueryBo bo, PageQuery pageQuery);

    List<KaisiBrandVo> listBrandOptions();

    Long addBrand(KaisiBrandSaveBo bo);

    void editBrand(KaisiBrandSaveBo bo);

    void deleteBrand(Long id);

    TableDataInfo<KaisiQualityVo> listQualities(KaisiQualityQueryBo bo, PageQuery pageQuery);

    List<KaisiQualityVo> listQualityOptions();

    Long addQuality(KaisiQualitySaveBo bo);

    void editQuality(KaisiQualitySaveBo bo);

    void deleteQuality(Long id);

    TableDataInfo<KaisiQualityBrandLinkVo> listQualityBrandLinks(KaisiQualityBrandLinkQueryBo bo, PageQuery pageQuery);

    Long addQualityBrandLink(KaisiQualityBrandLinkSaveBo bo);

    void editQualityBrandLink(KaisiQualityBrandLinkSaveBo bo);

    void deleteQualityBrandLink(Long id);
}

