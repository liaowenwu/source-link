package org.dromara.system.mapper.kaisi;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.dromara.system.domain.kaisi.OnlineOrderKaisiQuoteItem;
import org.dromara.system.domain.vo.kaisi.KaisiHistoryPartVo;
import org.dromara.system.domain.vo.kaisi.KaisiPriceTrendPointVo;

import java.util.List;

/**
 * 开思报价单明细 Mapper
 */
public interface OnlineOrderKaisiQuoteItemMapper extends BaseMapper<OnlineOrderKaisiQuoteItem> {

    /**
     * 历史零件报价统计
     */
    @Select({
        "<script>",
        "SELECT",
        " qi.parts_num AS partsNum,",
        " max(qi.parts_name) AS partsName,",
        " coalesce(qi.brand_name, '') AS brandName,",
        " coalesce(qi.parts_brand_quality, '') AS partsBrandQuality,",
        " count(1)::int AS quoteTimes,",
        " avg(qi.final_price) AS avgFinalPrice,",
        " max(q.last_log_time) AS latestQuoteTime",
        "FROM online_order_kaisi_quote_item qi",
        "LEFT JOIN online_order_kaisi_quotation q",
        "  ON q.quotation_id = qi.quotation_id",
        " AND coalesce(q.store_id, '') = coalesce(qi.store_id, '')",
        "WHERE 1 = 1",
        "<if test='beginTime != null and beginTime != \"\"'>",
        "  AND q.last_log_time &gt;= #{beginTime}::timestamp",
        "</if>",
        "<if test='endTime != null and endTime != \"\"'>",
        "  AND q.last_log_time &lt;= #{endTime}::timestamp",
        "</if>",
        "<if test='quotationId != null and quotationId != \"\"'>",
        "  AND qi.quotation_id LIKE concat('%', #{quotationId}, '%')",
        "</if>",
        "<if test='partsKeyword != null and partsKeyword != \"\"'>",
        "  AND (qi.parts_num LIKE concat('%', #{partsKeyword}, '%') OR qi.parts_name LIKE concat('%', #{partsKeyword}, '%'))",
        "</if>",
        "GROUP BY qi.parts_num, coalesce(qi.brand_name, ''), coalesce(qi.parts_brand_quality, '')",
        "ORDER BY max(q.last_log_time) DESC",
        "LIMIT 500",
        "</script>"
    })
    List<KaisiHistoryPartVo> selectHistoryPartStats(@Param("beginTime") String beginTime,
                                                    @Param("endTime") String endTime,
                                                    @Param("quotationId") String quotationId,
                                                    @Param("partsKeyword") String partsKeyword);

    /**
     * 查询零件价格走势
     */
    @Select({
        "<script>",
        "SELECT",
        " q.quotation_id AS quotationId,",
        " q.store_id AS storeId,",
        " qi.parts_num AS partsNum,",
        " qi.parts_name AS partsName,",
        " qi.brand_name AS brandName,",
        " qi.parts_brand_quality AS partsBrandQuality,",
        " qi.suggested_price AS suggestedPrice,",
        " qi.final_price AS finalPrice,",
        " q.last_log_time AS quoteTime",
        "FROM online_order_kaisi_quote_item qi",
        "LEFT JOIN online_order_kaisi_quotation q",
        "  ON q.quotation_id = qi.quotation_id",
        " AND coalesce(q.store_id, '') = coalesce(qi.store_id, '')",
        "WHERE qi.parts_num = #{partsNum}",
        "<if test='beginTime != null and beginTime != \"\"'>",
        "  AND q.last_log_time &gt;= #{beginTime}::timestamp",
        "</if>",
        "<if test='endTime != null and endTime != \"\"'>",
        "  AND q.last_log_time &lt;= #{endTime}::timestamp",
        "</if>",
        "<if test='quotationId != null and quotationId != \"\"'>",
        "  AND q.quotation_id LIKE concat('%', #{quotationId}, '%')",
        "</if>",
        "<if test='brandName != null and brandName != \"\"'>",
        "  AND qi.brand_name = #{brandName}",
        "</if>",
        "<if test='partsBrandQuality != null and partsBrandQuality != \"\"'>",
        "  AND qi.parts_brand_quality = #{partsBrandQuality}",
        "</if>",
        "ORDER BY q.last_log_time ASC",
        "LIMIT 1000",
        "</script>"
    })
    List<KaisiPriceTrendPointVo> selectPriceTrend(@Param("beginTime") String beginTime,
                                                  @Param("endTime") String endTime,
                                                  @Param("quotationId") String quotationId,
                                                  @Param("partsNum") String partsNum,
                                                  @Param("brandName") String brandName,
                                                  @Param("partsBrandQuality") String partsBrandQuality);
}
