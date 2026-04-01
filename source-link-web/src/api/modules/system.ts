import http from '@/api/http'
import type {
  ApiResult,
  DeptForm,
  DeptVO,
  MenuForm,
  RoleDeptPayload,
  MenuTreePayload,
  MenuVO,
  PageQuery,
  PageResult,
  PostForm,
  PostVO,
  RoleForm,
  RoleVO,
  TenantForm,
  TenantPackageForm,
  TenantPackageVO,
  TenantVO,
  TreeOptionNode,
  UserEditPayload,
  UserForm,
  UserVO,
} from '@/types/common'

export function listUsers(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<UserVO>>('/system/user/list', { params })
}

export function getUser(userId?: string | number) {
  return http.get<string, ApiResult<UserEditPayload>>(`/system/user/${userId ?? ''}`)
}

export function createUser(payload: UserForm) {
  return http.post<string, ApiResult<null>>('/system/user', payload)
}

export function updateUser(payload: UserForm) {
  return http.put<string, ApiResult<null>>('/system/user', payload)
}

export function deleteUser(userId: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/user/${userId}`)
}

export function resetUserPassword(userId: string | number, password: string) {
  return http.put<string, ApiResult<null>>('/system/user/resetPwd', { userId, password }, {
    encrypt: true,
    skipRepeatSubmit: true,
  })
}

export function changeUserStatus(userId: string | number, status: string) {
  return http.put<string, ApiResult<null>>('/system/user/changeStatus', { userId, status })
}

export function userDeptTree() {
  return http.get<string, ApiResult<TreeOptionNode[]>>('/system/user/deptTree')
}

export function listRoles(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<RoleVO>>('/system/role/list', { params })
}

export function getRole(roleId: string | number) {
  return http.get<string, ApiResult<RoleVO>>(`/system/role/${roleId}`)
}

export function createRole(payload: RoleForm) {
  return http.post<string, ApiResult<null>>('/system/role', payload)
}

export function updateRole(payload: RoleForm) {
  return http.put<string, ApiResult<null>>('/system/role', payload)
}

export function deleteRole(roleId: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/role/${roleId}`)
}

export function changeRoleStatus(roleId: string | number, status: string) {
  return http.put<string, ApiResult<null>>('/system/role/changeStatus', { roleId, status })
}

export function roleMenuTree(roleId: string | number) {
  return http.get<string, ApiResult<MenuTreePayload>>(`/system/menu/roleMenuTreeselect/${roleId}`)
}

export function roleDeptTree(roleId: string | number) {
  return http.get<string, ApiResult<RoleDeptPayload>>(`/system/role/deptTree/${roleId}`)
}

export function updateRoleDataScope(payload: RoleForm) {
  return http.put<string, ApiResult<null>>('/system/role/dataScope', payload)
}

export function listDepts(params?: Record<string, unknown>) {
  return http.get<string, ApiResult<DeptVO[]>>('/system/dept/list', { params })
}

export function deptTreeSelect() {
  return http.get<string, ApiResult<TreeOptionNode[]>>('/system/dept/optionselect')
}

export function getDept(deptId: string | number) {
  return http.get<string, ApiResult<DeptVO>>(`/system/dept/${deptId}`)
}

export function listDeptExcludeChild(deptId: string | number) {
  return http.get<string, ApiResult<DeptVO[]>>(`/system/dept/list/exclude/${deptId}`)
}

export function createDept(payload: DeptForm) {
  return http.post<string, ApiResult<null>>('/system/dept', payload)
}

export function updateDept(payload: DeptForm) {
  return http.put<string, ApiResult<null>>('/system/dept', payload)
}

export function deleteDept(deptId: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/dept/${deptId}`)
}

export function listMenus(params?: Record<string, unknown>) {
  return http.get<string, ApiResult<MenuVO[]>>('/system/menu/list', { params })
}

export function getMenu(menuId: string | number) {
  return http.get<string, ApiResult<MenuVO>>(`/system/menu/${menuId}`)
}

export function menuTreeSelect() {
  return http.get<string, ApiResult<TreeOptionNode[]>>('/system/menu/treeselect')
}

export function createMenu(payload: MenuForm) {
  return http.post<string, ApiResult<null>>('/system/menu', payload)
}

export function updateMenu(payload: MenuForm) {
  return http.put<string, ApiResult<null>>('/system/menu', payload)
}

export function deleteMenu(menuId: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/menu/${menuId}`)
}

export function cascadeDeleteMenu(menuIds: Array<string | number>) {
  return http.delete<string, ApiResult<null>>(`/system/menu/cascade/${menuIds.join(',')}`)
}

export function listPosts(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<PostVO>>('/system/post/list', { params })
}

export function getPost(postId: string | number) {
  return http.get<string, ApiResult<PostVO>>(`/system/post/${postId}`)
}

export function createPost(payload: PostForm) {
  return http.post<string, ApiResult<null>>('/system/post', payload)
}

export function updatePost(payload: PostForm) {
  return http.put<string, ApiResult<null>>('/system/post', payload)
}

export function deletePost(postId: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/post/${postId}`)
}

export function postDeptTree() {
  return http.get<string, ApiResult<TreeOptionNode[]>>('/system/post/deptTree')
}

export function listTenants(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<TenantVO>>('/system/tenant/list', { params })
}

export function getTenant(id: string | number) {
  return http.get<string, ApiResult<TenantVO>>(`/system/tenant/${id}`)
}

export function createTenant(payload: TenantForm) {
  return http.post<string, ApiResult<null>>('/system/tenant', payload, {
    encrypt: true,
    skipRepeatSubmit: true,
  })
}

export function updateTenant(payload: TenantForm) {
  return http.put<string, ApiResult<null>>('/system/tenant', payload)
}

export function deleteTenant(id: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/tenant/${id}`)
}

export function changeTenantStatus(id: string | number, tenantId: string | number, status: string) {
  return http.put<string, ApiResult<null>>('/system/tenant/changeStatus', { id, tenantId, status })
}

export function syncTenantPackage(tenantId: string | number, packageId: string | number) {
  return http.get<string, ApiResult<null>>('/system/tenant/syncTenantPackage', {
    params: { tenantId, packageId },
  })
}

export function syncTenantDict() {
  return http.get<string, ApiResult<null>>('/system/tenant/syncTenantDict')
}

export function syncTenantConfig() {
  return http.get<string, ApiResult<null>>('/system/tenant/syncTenantConfig')
}

export function listTenantPackages(params: Record<string, unknown> & PageQuery) {
  return http.get<string, PageResult<TenantPackageVO>>('/system/tenant/package/list', { params })
}

export function selectTenantPackages() {
  return http.get<string, ApiResult<TenantPackageVO[]>>('/system/tenant/package/selectList')
}

export function getTenantPackage(packageId: string | number) {
  return http.get<string, ApiResult<TenantPackageVO>>(`/system/tenant/package/${packageId}`)
}

export function createTenantPackage(payload: TenantPackageForm) {
  return http.post<string, ApiResult<null>>('/system/tenant/package', {
    ...payload,
    menuIds: payload.menuIds.join(','),
  })
}

export function updateTenantPackage(payload: TenantPackageForm) {
  return http.put<string, ApiResult<null>>('/system/tenant/package', {
    ...payload,
    menuIds: payload.menuIds.join(','),
  })
}

export function deleteTenantPackage(packageId: string | number) {
  return http.delete<string, ApiResult<null>>(`/system/tenant/package/${packageId}`)
}

export function changeTenantPackageStatus(packageId: string | number, status: string) {
  return http.put<string, ApiResult<null>>('/system/tenant/package/changeStatus', { packageId, status })
}

export function tenantPackageMenuTree(packageId: string | number) {
  return http.get<string, ApiResult<MenuTreePayload>>(`/system/menu/tenantPackageMenuTreeselect/${packageId}`)
}
