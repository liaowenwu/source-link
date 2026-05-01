package org.dromara.system.utils.kaisi;

import cn.hutool.core.convert.Convert;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * 开思模块 Map 读取工具
 *
 * 说明：统一处理 ingest 事件中的动态字段读取，避免 service 堆积工具逻辑。
 */
public class KaisiMapUtils {

    private KaisiMapUtils() {
    }

    public static String getString(Map<String, Object> source, String key) {
        if (source == null || StrUtil.isBlank(key)) {
            return StrUtil.EMPTY;
        }
        return StrUtil.trim(Convert.toStr(source.get(key), StrUtil.EMPTY));
    }

    public static Integer getInteger(Map<String, Object> source, String key, Integer defaultValue) {
        if (source == null || StrUtil.isBlank(key)) {
            return defaultValue;
        }
        Integer value = Convert.toInt(source.get(key));
        return ObjectUtil.defaultIfNull(value, defaultValue);
    }

    public static Long getLong(Map<String, Object> source, String key, Long defaultValue) {
        if (source == null || StrUtil.isBlank(key)) {
            return defaultValue;
        }
        Long value = Convert.toLong(source.get(key));
        return ObjectUtil.defaultIfNull(value, defaultValue);
    }

    public static Boolean getBoolean(Map<String, Object> source, String key, Boolean defaultValue) {
        if (source == null || StrUtil.isBlank(key)) {
            return defaultValue;
        }
        Boolean value = Convert.toBool(source.get(key));
        return ObjectUtil.defaultIfNull(value, defaultValue);
    }

    public static BigDecimal getBigDecimal(Map<String, Object> source, String key) {
        if (source == null || StrUtil.isBlank(key)) {
            return null;
        }
        return Convert.toBigDecimal(source.get(key));
    }

    @SuppressWarnings("unchecked")
    public static Map<String, Object> getMap(Map<String, Object> source, String key) {
        if (source == null || StrUtil.isBlank(key)) {
            return Collections.emptyMap();
        }
        Object value = source.get(key);
        if (value instanceof Map<?, ?> valueMap) {
            return (Map<String, Object>) valueMap;
        }
        return Collections.emptyMap();
    }

    @SuppressWarnings("unchecked")
    public static List<Map<String, Object>> getMapList(Map<String, Object> source, String key) {
        if (source == null || StrUtil.isBlank(key)) {
            return Collections.emptyList();
        }
        Object value = source.get(key);
        if (value instanceof List<?> list) {
            return (List<Map<String, Object>>) list;
        }
        return Collections.emptyList();
    }
}

