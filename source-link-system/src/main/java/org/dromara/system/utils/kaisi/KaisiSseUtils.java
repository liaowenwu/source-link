package org.dromara.system.utils.kaisi;

import cn.hutool.json.JSONUtil;
import org.dromara.common.sse.utils.SseMessageUtils;

import java.util.HashMap;
import java.util.Map;

/**
 * 开思 SSE 推送工具
 */
public class KaisiSseUtils {

    private KaisiSseUtils() {
    }

    public static void publish(String topic, String event, String taskNo, Map<String, Object> payload) {
        Map<String, Object> body = new HashMap<>(8);
        body.put("topic", topic);
        body.put("event", event);
        body.put("taskNo", taskNo);
        body.put("payload", payload);
        SseMessageUtils.publishAll(JSONUtil.toJsonStr(body));
    }
}

