-- 开思工作台「基础配置」菜单修正脚本（PostgreSQL）
-- 可重复执行：用于新增/修正用户侧基础配置菜单与按钮权限。
DO
$$
DECLARE
    v_now             TIMESTAMP := NOW();
    v_root_menu_id    BIGINT;
    v_setting_menu_id BIGINT;
    v_admin_role_id   BIGINT;
BEGIN
    -- 1) 确保开思工作台根菜单存在
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
            'system', v_now, '', NULL, '开思工作台根菜单'
        );
    END IF;

    -- 2) 新增或修正用户侧基础配置菜单，组件沿用已开发页面 kaisi/workbench/settings
    SELECT menu_id
    INTO v_setting_menu_id
    FROM sys_menu
    WHERE component = 'kaisi/workbench/settings'
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
            'system', v_now, '', NULL, '开思工作台用户侧基础配置'
        );
    ELSE
        UPDATE sys_menu
        SET parent_id = v_root_menu_id,
            menu_name = '基础配置',
            order_num = 5,
            path = 'settings',
            component = 'kaisi/workbench/settings',
            perms = 'kaisi:workbench:setting:query',
            icon = 'setting',
            visible = '0',
            status = '0',
            update_by = 'system',
            update_time = v_now,
            remark = '开思工作台用户侧基础配置'
        WHERE menu_id = v_setting_menu_id;
    END IF;

    -- 3) 查询按钮权限
    IF NOT EXISTS (
        SELECT 1 FROM sys_menu
        WHERE parent_id = v_setting_menu_id
          AND perms = 'kaisi:workbench:setting:query'
          AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_setting_menu_id, '基础配置查询', 1, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:setting:query', '#',
            'system', v_now, '', NULL, '开思工作台基础配置查询按钮'
        );
    ELSE
        UPDATE sys_menu
        SET menu_name = '基础配置查询', update_by = 'system', update_time = v_now
        WHERE parent_id = v_setting_menu_id
          AND perms = 'kaisi:workbench:setting:query'
          AND menu_type = 'F';
    END IF;

    -- 4) 保存按钮权限
    IF NOT EXISTS (
        SELECT 1 FROM sys_menu
        WHERE parent_id = v_setting_menu_id
          AND perms = 'kaisi:workbench:setting:edit'
          AND menu_type = 'F'
    ) THEN
        INSERT INTO sys_menu (
            menu_id, parent_id, menu_name, order_num, path, component, query_param,
            is_frame, is_cache, menu_type, visible, status, perms, icon,
            create_by, create_time, update_by, update_time, remark
        ) VALUES (
            (SELECT COALESCE(MAX(menu_id), 0) + 1 FROM sys_menu), v_setting_menu_id, '基础配置保存', 2, '#', NULL, NULL,
            '1', '1', 'F', '0', '0', 'kaisi:workbench:setting:edit', '#',
            'system', v_now, '', NULL, '开思工作台基础配置保存按钮'
        );
    ELSE
        UPDATE sys_menu
        SET menu_name = '基础配置保存', update_by = 'system', update_time = v_now
        WHERE parent_id = v_setting_menu_id
          AND perms = 'kaisi:workbench:setting:edit'
          AND menu_type = 'F';
    END IF;

    -- 5) 给 admin 角色补授权
    SELECT role_id INTO v_admin_role_id FROM sys_role WHERE role_key = 'admin' LIMIT 1;
    IF v_admin_role_id IS NOT NULL THEN
        INSERT INTO sys_role_menu(role_id, menu_id)
        SELECT v_admin_role_id, m.menu_id
        FROM sys_menu m
        WHERE (m.menu_id = v_setting_menu_id OR m.parent_id = v_setting_menu_id)
          AND NOT EXISTS (
              SELECT 1
              FROM sys_role_menu rm
              WHERE rm.role_id = v_admin_role_id
                AND rm.menu_id = m.menu_id
          );
    END IF;
END
$$;
