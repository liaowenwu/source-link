-- 开思工作台菜单与权限脚本（PostgreSQL）
-- 说明：
-- 1. 本脚本仅维护 sys_menu / sys_role_menu，不包含建表与初始化业务数据。
-- 2. 采用幂等写法，可重复执行。

DO
$$
DECLARE
    v_now            TIMESTAMP := NOW();
    v_root_menu_id   BIGINT;
    v_dash_menu_id   BIGINT;
    v_quote_menu_id  BIGINT;
    v_manual_menu_id BIGINT;
    v_history_menu_id BIGINT;
    v_setting_menu_id BIGINT;
    v_admin_role_id  BIGINT;
BEGIN
    -- 1) 一级目录：开思工作台
    SELECT menu_id
    INTO v_root_menu_id
    FROM sys_menu
    WHERE menu_type = 'M'
      AND path = 'kaisi'
    LIMIT 1;

    IF v_root_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_root_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_root_menu_id, 0, '开思工作台', 90, 'kaisi', NULL, NULL,
            '1', '1', 'M', '0', '0', NULL, 'monitor',
            'system', v_now, '', NULL, '开思工作台目录'
        );
    END IF;

    -- 2) 工作台首页
    SELECT menu_id
    INTO v_dash_menu_id
    FROM sys_menu
    WHERE parent_id = v_root_menu_id
      AND component = 'kaisi/workbench/index'
      AND menu_type = 'C'
    LIMIT 1;

    IF v_dash_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_dash_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_dash_menu_id, v_root_menu_id, '工作台首页', 1, 'workbench', 'kaisi/workbench/index', NULL,
            '1', '1', 'C', '0', '0', 'kaisi:workbench:dashboard', 'dashboard',
            'system', v_now, '', NULL, '开思工作台首页'
        );
    END IF;

    -- 3) 报价单管理
    SELECT menu_id
    INTO v_quote_menu_id
    FROM sys_menu
    WHERE parent_id = v_root_menu_id
      AND component = 'kaisi/workbench/quotation'
      AND menu_type = 'C'
    LIMIT 1;

    IF v_quote_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_quote_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_quote_menu_id, v_root_menu_id, '报价单管理', 2, 'quotation', 'kaisi/workbench/quotation', NULL,
            '1', '1', 'C', '0', '0', 'kaisi:workbench:quotation:list', 'form',
            'system', v_now, '', NULL, '开思报价单管理'
        );
    END IF;

    -- 4) 人工补价
    SELECT menu_id
    INTO v_manual_menu_id
    FROM sys_menu
    WHERE parent_id = v_root_menu_id
      AND component = 'kaisi/workbench/manual'
      AND menu_type = 'C'
    LIMIT 1;

    IF v_manual_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_manual_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_manual_menu_id, v_root_menu_id, '人工补价', 3, 'manual', 'kaisi/workbench/manual', NULL,
            '1', '1', 'C', '0', '0', 'kaisi:workbench:manual:edit', 'edit',
            'system', v_now, '', NULL, '开思人工补价'
        );
    END IF;

    -- 5) 历史报价单
    SELECT menu_id
    INTO v_history_menu_id
    FROM sys_menu
    WHERE parent_id = v_root_menu_id
      AND component = 'kaisi/workbench/history'
      AND menu_type = 'C'
    LIMIT 1;

    IF v_history_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_history_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_history_menu_id, v_root_menu_id, '历史报价单', 4, 'history', 'kaisi/workbench/history', NULL,
            '1', '1', 'C', '0', '0', 'kaisi:workbench:dashboard', 'history',
            'system', v_now, '', NULL, '开思历史报价单'
        );
    END IF;

    -- 6) 基础配置（用户侧配置）
    SELECT menu_id
    INTO v_setting_menu_id
    FROM sys_menu
    WHERE parent_id = v_root_menu_id
      AND component = 'kaisi/workbench/settings'
      AND menu_type = 'C'
    LIMIT 1;

    IF v_setting_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_setting_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_setting_menu_id, v_root_menu_id, '基础配置', 5, 'settings', 'kaisi/workbench/settings', NULL,
            '1', '1', 'C', '0', '0', 'kaisi:workbench:setting:query', 'setting',
            'system', v_now, '', NULL, '开思工作台用户设置'
        );
    END IF;

    -- 7) 按钮权限（基础配置下）
    IF NOT EXISTS (
        SELECT 1 FROM sys_menu WHERE parent_id = v_setting_menu_id AND perms = 'kaisi:workbench:setting:query' AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_setting_menu_id, '基础配置查询', 1, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:setting:query', '#',
            'system', v_now, '', NULL, '开思基础配置查询按钮'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM sys_menu WHERE parent_id = v_setting_menu_id AND perms = 'kaisi:workbench:setting:edit' AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_setting_menu_id, '基础配置保存', 2, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:setting:edit', '#',
            'system', v_now, '', NULL, '开思基础配置保存按钮'
        );
    END IF;

    -- 8) 按钮权限（报价单管理下）
    IF NOT EXISTS (
        SELECT 1 FROM sys_menu WHERE parent_id = v_quote_menu_id AND perms = 'kaisi:workbench:quotation:query' AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_quote_menu_id, '报价单查询', 1, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:quotation:query', '#',
            'system', v_now, '', NULL, '开思报价单查询按钮'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM sys_menu WHERE parent_id = v_quote_menu_id AND perms = 'kaisi:workbench:quotation:submit' AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_quote_menu_id, '报价单提交', 2, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:quotation:submit', '#',
            'system', v_now, '', NULL, '开思报价单提交按钮'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM sys_menu WHERE parent_id = v_quote_menu_id AND perms = 'kaisi:workbench:quotation:retry' AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_quote_menu_id, '报价单重试', 3, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:quotation:retry', '#',
            'system', v_now, '', NULL, '开思报价单重试按钮'
        );
    END IF;

    -- 9) 按钮权限（人工补价下）
    IF NOT EXISTS (
        SELECT 1 FROM sys_menu WHERE parent_id = v_manual_menu_id AND perms = 'kaisi:workbench:manual:edit' AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_manual_menu_id, '人工补价保存', 1, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:manual:edit', '#',
            'system', v_now, '', NULL, '开思人工补价保存按钮'
        );
    END IF;

    -- 10) 管理员角色授权（可按需保留）
    SELECT role_id INTO v_admin_role_id FROM sys_role WHERE role_key = 'admin' LIMIT 1;
    IF v_admin_role_id IS NOT NULL THEN
        INSERT INTO sys_role_menu(role_id, menu_id)
        SELECT v_admin_role_id, m.menu_id
        FROM sys_menu m
        WHERE (m.menu_id = v_root_menu_id OR m.parent_id = v_root_menu_id OR m.perms LIKE 'kaisi:workbench:%')
          AND NOT EXISTS (
              SELECT 1
              FROM sys_role_menu rm
              WHERE rm.role_id = v_admin_role_id
                AND rm.menu_id = m.menu_id
          );
    END IF;
END
$$;

