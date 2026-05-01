package org.dromara.system.domain.kaisi;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.dromara.common.tenant.core.TenantEntity;

/**
 * 开思质量配置
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("kaisi_quality")
public class KaisiQuality extends TenantEntity {

    @TableId(value = "id")
    private Long id;

    /**
     * 质量编码
     */
    private String qualityCode;

    /**
     * 质量名称
     */
    private String qualityName;

    /**
     * 开思原始质量ID
     */
    private String qualityOriginId;

    /**
     * 质量类型
     */
    private Integer qualityType;

    /**
     * 排序号
     */
    private Integer orderNum;

    /**
     * 状态（1启用 0停用）
     */
    private Integer status;
}

