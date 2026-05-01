-- 开思平台配置页面菜单脚本（PostgreSQL）
-- 说明：
-- 1. 仅维护“系统管理/开思平台配置”菜单及其按钮权限；
-- 2. 幂等写法，可重复执行；
-- 3. 不包含建表和业务初始化数据。

DO
$$
DECLARE
    v_now                 TIMESTAMP := NOW();
    v_system_menu_id      BIGINT;
    v_base_config_menu_id BIGINT;
    v_admin_role_id       BIGINT;
BEGIN
    -- 1) 一级目录：系统管理（通常由系统内置菜单提供）
    SELECT menu_id
    INTO v_system_menu_id
    FROM sys_menu
    WHERE menu_type = 'M'
      AND path = 'system'
    LIMIT 1;

    IF v_system_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_system_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_system_menu_id, 0, '系统管理', 1, 'system', NULL, NULL,
            '1', '1', 'M', '0', '0', NULL, 'system',
            'system', v_now, '', NULL, '系统管理目录'
        );
    END IF;

    -- 2) 子菜单：开思平台配置（不存在则新增；存在旧工作台基础配置则迁移到系统管理下）
    SELECT menu_id
    INTO v_base_config_menu_id
    FROM sys_menu
    WHERE component = 'kaisi/workbench/base-config'
      AND menu_type = 'C'
    LIMIT 1;

    IF v_base_config_menu_id IS NULL THEN
        SELECT COALESCE(MAX(menu_id), 0) + 1 INTO v_base_config_menu_id FROM sys_menu;
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            v_base_config_menu_id, v_system_menu_id, '开思平台配置', 90, 'kaisi-base-config', 'kaisi/workbench/base-config', NULL,
            '1', '1', 'C', '0', '0', 'kaisi:base-config:query', 'setting',
            'system', v_now, '', NULL, '开思平台基础配置'
        );
    ELSE
        UPDATE sys_menu
        SET parent_id = v_system_menu_id,
            menu_name = '开思平台配置',
            path = 'kaisi-base-config',
            order_num = 90,
            perms = 'kaisi:base-config:query',
            update_by = 'system',
            update_time = v_now,
            remark = '开思平台基础配置'
        WHERE menu_id = v_base_config_menu_id;
    END IF;

    -- 3) 按钮权限：查询
    IF NOT EXISTS (
        SELECT 1
        FROM sys_menu
        WHERE parent_id = v_base_config_menu_id
          AND perms = 'kaisi:base-config:query'
          AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_base_config_menu_id, '基础配置查询', 1, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:base-config:query', '#',
            'system', v_now, '', NULL, '开思基础配置查询按钮'
        );
    END IF;

    -- 4) 按钮权限：编辑
    IF NOT EXISTS (
        SELECT 1
        FROM sys_menu
        WHERE parent_id = v_base_config_menu_id
          AND perms = 'kaisi:base-config:edit'
          AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_base_config_menu_id, '基础配置编辑', 2, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:base-config:edit', '#',
            'system', v_now, '', NULL, '开思基础配置编辑按钮'
        );
    END IF;

    -- 5) 自动授权管理员角色
    SELECT role_id INTO v_admin_role_id FROM sys_role WHERE role_key = 'admin' LIMIT 1;
    IF v_admin_role_id IS NOT NULL THEN
        INSERT INTO sys_role_menu(role_id, menu_id)
        SELECT v_admin_role_id, m.menu_id
        FROM sys_menu m
        WHERE (m.menu_id = v_base_config_menu_id OR m.parent_id = v_base_config_menu_id)
          AND NOT EXISTS (
              SELECT 1
              FROM sys_role_menu rm
              WHERE rm.role_id = v_admin_role_id
                AND rm.menu_id = m.menu_id
          );
    END IF;
END
$$;
