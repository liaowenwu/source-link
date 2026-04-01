export interface NavItem {
  key: string
  label: string
  path: string
  icon: string
  group: string
  description: string
}

export const navItems: NavItem[] = [
  {
    key: 'overview',
    label: '工作台',
    path: '/overview',
    icon: 'solar:chart-square-bold-duotone',
    group: '总览',
    description: '查看系统运行概况、在线人数和常用入口。',
  },

  {
    key: 'users',
    label: '用户管理',
    path: '/system/users',
    icon: 'solar:users-group-rounded-bold-duotone',
    group: '系统管理',
    description: '维护平台用户、角色分配、岗位信息和账号状态。',
  },
  {
    key: 'roles',
    label: '角色管理',
    path: '/system/roles',
    icon: 'solar:shield-keyhole-bold-duotone',
    group: '系统管理',
    description: '维护角色、菜单权限和数据权限范围。',
  },
  {
    key: 'depts',
    label: '部门管理',
    path: '/system/depts',
    icon: 'solar:buildings-3-bold-duotone',
    group: '系统管理',
    description: '维护组织架构、上下级关系和部门负责人信息。',
  },
  {
    key: 'menus',
    label: '菜单管理',
    path: '/system/menus',
    icon: 'solar:hamburger-menu-bold-duotone',
    group: '系统管理',
    description: '维护目录、菜单、按钮和前端路由配置。',
  },
  {
    key: 'posts',
    label: '岗位管理',
    path: '/system/posts',
    icon: 'solar:case-round-bold-duotone',
    group: '系统管理',
    description: '维护岗位编码、岗位分类、所属部门和状态。',
  },

  {
    key: 'tenants',
    label: '租户管理',
    path: '/tenant/tenants',
    icon: 'solar:buildings-bold-duotone',
    group: '租户中心',
    description: '维护租户资料、套餐绑定、到期时间和状态。',
  },
  {
    key: 'tenant-packages',
    label: '租户套餐',
    path: '/tenant/packages',
    icon: 'solar:box-bold-duotone',
    group: '租户中心',
    description: '维护套餐名称、菜单权限和可用状态。',
  },

  {
    key: 'online',
    label: '在线用户',
    path: '/monitor/online',
    icon: 'solar:monitor-bold-duotone',
    group: '系统监控',
    description: '查看当前在线会话、登录来源和设备信息。',
  },
  {
    key: 'cache',
    label: '缓存监控',
    path: '/monitor/cache',
    icon: 'solar:database-bold-duotone',
    group: '系统监控',
    description: '查看 Redis 缓存信息、统计和命令情况。',
  },
  {
    key: 'operlog',
    label: '操作日志',
    path: '/monitor/operlog',
    icon: 'solar:document-text-bold-duotone',
    group: '系统监控',
    description: '查看业务操作记录、接口信息和执行结果。',
  },
  {
    key: 'loginlog',
    label: '登录日志',
    path: '/monitor/loginlog',
    icon: 'solar:login-3-bold-duotone',
    group: '系统监控',
    description: '查看登录记录、登录地点和异常提示。',
  },
  {
    key: 'monitor-center',
    label: '监控中心',
    path: '/monitor/center',
    icon: 'solar:window-frame-bold-duotone',
    group: '系统监控',
    description: '查看服务实例监控面板和运维入口。',
  },
]
