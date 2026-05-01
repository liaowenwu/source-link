package org.dromara.system.utils.kaisi;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.convert.Convert;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONUtil;

import java.util.*;

/**
 * 开思抓价配置构建工具
 */
public class KaisiCrawlerConfigBuildUtils {

    private KaisiCrawlerConfigBuildUtils() {
    }

    /**
     * 构建单个平台配置
     */
    public static Map<String, Object> buildPlatformConfig(
        String platformCode,
        Map<String, Object> mainConfig
    ) {
        Map<String, Object> config = new HashMap<>(24);
        config.put("platformCode", StrUtil.blankToDefault(platformCode, StrUtil.EMPTY));
        config.put("crawlStrategyType", stringValue(mainConfig, "crawlStrategyType", "FULL_SELECTED"));
        config.put("crawlStrategySelectedPlatformCodes", parseTextList(mainConfig, "crawlStrategySelectedPlatformCodesJson"));
        config.put("crawlStrategyPriorityPlatformCodes", parseTextList(mainConfig, "crawlStrategyPriorityPlatformCodesJson"));
        config.put("crawlStrategyStopOnHit", Convert.toBool(mainConfig.get("crawlStrategyStopOnHit"), false));
        config.put("defaultCity", stringValue(mainConfig, "defaultCity", StrUtil.EMPTY));
        config.put("priceAdvantageRate", Convert.toDouble(mainConfig.get("priceAdvantageRate"), 5.0D));
        config.put("defaultMarkupRate", Convert.toDouble(mainConfig.get("defaultMarkupRate"), 0.0D));
        config.put("defaultTransferDays", Convert.toInt(mainConfig.get("defaultTransferDays"), 0));
        config.put("singleSkuMaxCrawlCount", Convert.toInt(mainConfig.get("singleSkuMaxCrawlCount"), 0));

        List<Long> qualityIds = new ArrayList<>();
        List<String> qualityOriginIds = parseTextList(mainConfig, "qualityOriginIdsJson");
        config.put("qualityIds", qualityIds);
        config.put("qualityOriginIds", qualityOriginIds);

        List<String> brandOriginIds = parseTextList(mainConfig, "brandOriginIdsJson");
        config.put("brandOriginIds", brandOriginIds);
        config.put("brandNames", Collections.emptyList());

        List<String> regionOriginIds = parseTextList(mainConfig, "regionOriginIdsJson");
        config.put("regionOriginIds", regionOriginIds);
        config.put("regionNames", Collections.emptyList());
        config.put("regionExtraDays", parseIntMap(mainConfig, "regionExtraDaysJson"));

        List<Map<String, Object>> supplierConfigs = buildSupplierConfigs(mainConfig);
        config.put("supplierOriginIds", collectSupplierOriginIds(supplierConfigs));
        config.put("supplierNames", collectSupplierNames(supplierConfigs));
        config.put("supplierConfigs", supplierConfigs);
        return config;
    }

    /**
     * 组装根配置（兼容旧版 crawler-config 结构）
     */
    public static Map<String, Object> buildCrawlerConfigRoot(Map<String, Object> globalConfig, Map<String, Object> benbenConfig, Map<String, Object> robotConfig) {
        Map<String, Object> root = new HashMap<>(16);
        Map<String, Object> global = ObjectUtil.defaultIfNull(globalConfig, Collections.emptyMap());
        Map<String, Object> benben = ObjectUtil.defaultIfNull(benbenConfig, Collections.emptyMap());
        Map<String, Object> robot = ObjectUtil.defaultIfNull(robotConfig, Collections.emptyMap());
        root.put("selectedPlatformCodes", parseTextList(global, "selectedPlatformCodesJson"));
        root.put("crawlStrategyType", stringValue(global, "crawlStrategyType", "ALL"));
        root.put("autoPriceEnabled", Convert.toBool(global.get("autoPriceEnabled"), true));
        root.put("autoSubmitEnabled", Convert.toBool(global.get("autoSubmitEnabled"), false));
        root.put("quotationCrawlConcurrency", Convert.toInt(global.get("quotationCrawlConcurrency"), 1));
        root.put("priceConcurrency", Convert.toInt(global.get("priceConcurrency"), 1));
        root.put("requestTimeoutMs", Convert.toInt(global.get("requestTimeoutMs"), 30000));
        root.put("retryTimes", Convert.toInt(global.get("retryTimes"), 3));
        root.put("maxQuotationProcessCount", Convert.toInt(global.get("maxQuotationProcessCount"), 0));
        root.put("manualPriceFillEnabled", Convert.toBool(global.get("manualPriceFillEnabled"), false));
        root.put("globalConfig", global);
        root.putAll(benben);
        root.put("robotConfig", robot);

        List<Map<String, Object>> platformConfigs = new ArrayList<>(2);
        platformConfigs.add(buildPlatformConfigNode("benben", benben));
        platformConfigs.add(buildPlatformConfigNode("robot", robot));
        root.put("platformConfigs", platformConfigs);
        root.put("platformConfigMap", Map.of("benben", benben, "robot", robot));
        return root;
    }

    public static Map<String, Object> buildCrawlerConfigRoot(Map<String, Object> benbenConfig, Map<String, Object> robotConfig) {
        return buildCrawlerConfigRoot(Collections.emptyMap(), benbenConfig, robotConfig);
    }

    private static Map<String, Object> buildPlatformConfigNode(String platformCode, Map<String, Object> config) {
        Map<String, Object> node = new HashMap<>(2);
        node.put("platformCode", platformCode);
        node.put("config", config);
        return node;
    }

    private static List<String> parseTextList(Map<String, Object> source, String key) {
        Object raw = source.get(key);
        if (raw == null) {
            return Collections.emptyList();
        }
        if (raw instanceof Collection<?> collection) {
            List<String> result = new ArrayList<>();
            for (Object item : collection) {
                String value = StrUtil.trim(Convert.toStr(item));
                if (StrUtil.isNotBlank(value) && !result.contains(value)) {
                    result.add(value);
                }
            }
            return result;
        }
        String text = StrUtil.trim(Convert.toStr(raw));
        if (StrUtil.isBlank(text)) {
            return Collections.emptyList();
        }
        if (!JSONUtil.isTypeJSONArray(text)) {
            return Arrays.stream(text.split(","))
                .map(StrUtil::trim)
                .filter(StrUtil::isNotBlank)
                .distinct()
                .toList();
        }
        JSONArray array = JSONUtil.parseArray(text);
        List<String> result = new ArrayList<>();
        for (Object item : array) {
            String value = StrUtil.trim(Convert.toStr(item));
            if (StrUtil.isNotBlank(value) && !result.contains(value)) {
                result.add(value);
            }
        }
        return result;
    }

    private static Map<String, Integer> parseIntMap(Map<String, Object> source, String key) {
        String text = StrUtil.trim(Convert.toStr(source.get(key)));
        if (StrUtil.isBlank(text) || !JSONUtil.isTypeJSONObject(text)) {
            return Collections.emptyMap();
        }
        Map<String, Integer> result = new LinkedHashMap<>();
        Map<String, Object> rawMap = JSONUtil.toBean(text, Map.class);
        for (Map.Entry<String, Object> entry : rawMap.entrySet()) {
            String mapKey = StrUtil.trim(entry.getKey());
            if (StrUtil.isBlank(mapKey)) {
                continue;
            }
            result.put(mapKey, Math.max(0, Convert.toInt(entry.getValue(), 0)));
        }
        return result;
    }

    private static String stringValue(Map<String, Object> source, String key, String defaultValue) {
        return StrUtil.blankToDefault(StrUtil.trim(Convert.toStr(source.get(key))), defaultValue);
    }

    private static List<Map<String, Object>> buildSupplierConfigs(Map<String, Object> mainConfig) {
        String jsonText = StrUtil.trim(Convert.toStr(mainConfig.get("supplierConfigsJson")));
        if (StrUtil.isNotBlank(jsonText) && JSONUtil.isTypeJSONArray(jsonText)) {
            JSONArray array = JSONUtil.parseArray(jsonText);
            List<Map<String, Object>> result = new ArrayList<>(array.size());
            for (Object item : array) {
                if (item instanceof Map<?, ?> map) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> typed = (Map<String, Object>) map;
                    appendSupplierConfig(result, typed);
                }
            }
            return result;
        }
        return Collections.emptyList();
    }

    /**
     * 用户配置按“品牌-商家”保存，爬虫侧按明细过滤和加价。
     */
    private static void appendSupplierConfig(List<Map<String, Object>> result, Map<String, Object> brandConfig) {
        String brandOriginId = StrUtil.trim(Convert.toStr(brandConfig.get("brandOriginId")));
        String brandName = StrUtil.trim(Convert.toStr(brandConfig.get("brandName")));
        Object suppliers = brandConfig.get("suppliers");
        if (suppliers instanceof Collection<?> collection) {
            for (Object supplier : collection) {
                if (supplier instanceof Map<?, ?> supplierMap) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> typedSupplier = (Map<String, Object>) supplierMap;
                    addSupplierBinding(result, brandOriginId, brandName, typedSupplier);
                }
            }
            return;
        }

        // 兼容历史格式：一个品牌下 supplierOriginIds 共用同一套加价/调货配置。
        Object supplierOriginIds = brandConfig.get("supplierOriginIds");
        if (supplierOriginIds instanceof Collection<?> collection) {
            for (Object supplierOriginId : collection) {
                Map<String, Object> supplier = new HashMap<>(4);
                supplier.put("supplierOriginId", supplierOriginId);
                supplier.put("markupRate", brandConfig.get("markupRate"));
                supplier.put("transferDays", brandConfig.get("transferDays"));
                addSupplierBinding(result, brandOriginId, brandName, supplier);
            }
            return;
        }

        // 兼容已展平格式。
        addSupplierBinding(result, brandOriginId, brandName, brandConfig);
    }

    private static void addSupplierBinding(List<Map<String, Object>> result, String brandOriginId, String brandName, Map<String, Object> supplier) {
        String supplierOriginId = StrUtil.trim(Convert.toStr(supplier.get("supplierOriginId")));
        if (StrUtil.isBlank(supplierOriginId)) {
            return;
        }
        Map<String, Object> row = new HashMap<>(8);
        row.put("brandOriginId", brandOriginId);
        row.put("brandName", brandName);
        row.put("supplierOriginId", supplierOriginId);
        row.put("supplierName", supplier.get("supplierName"));
        row.put("markupRate", supplier.get("markupRate"));
        row.put("transferDays", supplier.get("transferDays"));
        result.add(row);
    }

    private static List<String> collectSupplierOriginIds(List<Map<String, Object>> supplierConfigs) {
        List<String> result = new ArrayList<>();
        if (CollUtil.isEmpty(supplierConfigs)) {
            return result;
        }
        for (Map<String, Object> config : supplierConfigs) {
            addDistinctText(result, config.get("supplierOriginId"));
            addDistinctTextList(result, config.get("supplierOriginIds"));
        }
        return result;
    }

    private static List<String> collectSupplierNames(List<Map<String, Object>> supplierConfigs) {
        List<String> result = new ArrayList<>();
        if (CollUtil.isEmpty(supplierConfigs)) {
            return result;
        }
        for (Map<String, Object> config : supplierConfigs) {
            addDistinctText(result, config.get("supplierName"));
            addDistinctTextList(result, config.get("supplierNames"));
        }
        return result;
    }

    private static void addDistinctText(List<String> result, Object raw) {
        String value = StrUtil.trim(Convert.toStr(raw));
        if (StrUtil.isNotBlank(value) && !result.contains(value)) {
            result.add(value);
        }
    }

    private static void addDistinctTextList(List<String> result, Object raw) {
        if (raw instanceof Collection<?> collection) {
            for (Object item : collection) {
                addDistinctText(result, item);
            }
            return;
        }
        String text = StrUtil.trim(Convert.toStr(raw));
        if (StrUtil.isBlank(text)) {
            return;
        }
        if (JSONUtil.isTypeJSONArray(text)) {
            for (Object item : JSONUtil.parseArray(text)) {
                addDistinctText(result, item);
            }
            return;
        }
        for (String item : text.split(",")) {
            addDistinctText(result, item);
        }
    }
}
