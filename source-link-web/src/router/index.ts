import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { public: true, title: '登录' },
    },
    {
      path: '/',
      component: () => import('@/layouts/ConsoleLayout.vue'),
      children: [
        { path: '', redirect: '/overview' },
        { path: '/overview', name: 'overview', component: () => import('@/pages/OverviewPage.vue') },
        { path: '/system/users', name: 'users', component: () => import('@/pages/system/UsersPage.vue') },
        { path: '/system/roles', name: 'roles', component: () => import('@/pages/system/RolesPage.vue') },
        { path: '/system/depts', name: 'depts', component: () => import('@/pages/system/DeptsPage.vue') },
        { path: '/system/menus', name: 'menus', component: () => import('@/pages/system/MenusPage.vue') },
        { path: '/system/posts', name: 'posts', component: () => import('@/pages/system/PostsPage.vue') },
        { path: '/tenant/tenants', name: 'tenants', component: () => import('@/pages/tenant/TenantsPage.vue') },
        { path: '/tenant/packages', name: 'tenant-packages', component: () => import('@/pages/tenant/TenantPackagesPage.vue') },
        { path: '/monitor/online', name: 'online', component: () => import('@/pages/monitor/OnlineUsersPage.vue') },
        { path: '/monitor/cache', name: 'cache', component: () => import('@/pages/monitor/CacheMonitorPage.vue') },
        { path: '/monitor/operlog', name: 'operlog', component: () => import('@/pages/monitor/OperationLogsPage.vue') },
        { path: '/monitor/loginlog', name: 'loginlog', component: () => import('@/pages/monitor/LoginLogsPage.vue') },
        { path: '/monitor/center', name: 'monitor-center', component: () => import('@/pages/monitor/MonitorCenterPage.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  if (to.meta.public) {
    if (to.path === '/login' && authStore.isAuthenticated) {
      return '/overview'
    }
    return true
  }

  if (!authStore.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (!authStore.profile) {
    try {
      await authStore.refreshProfile()
    } catch {
      authStore.clearSession()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  return true
})

export default router
