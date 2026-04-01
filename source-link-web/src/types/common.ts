export interface ApiResult<T> {
  code: number
  msg: string
  data: T
}

export interface PageResult<T> {
  code: number
  msg: string
  total: number
  rows: T[]
}

export interface PageQuery {
  pageNum?: number
  pageSize?: number
  orderByColumn?: string
  isAsc?: string
}

export interface BaseEntity {
  createBy?: string
  createTime?: string
  updateBy?: string
  updateTime?: string
}

export interface TreeOptionNode {
  id: string | number
  label: string
  parentId?: string | number
  weight?: number
  disabled?: boolean
  children?: TreeOptionNode[]
}

export interface RoleVO extends BaseEntity {
  roleId: string | number
  roleName: string
  roleKey: string
  roleSort: number
  dataScope?: string
  status: string
  remark?: string
  menuCheckStrictly?: boolean
  deptCheckStrictly?: boolean
  menuIds?: Array<string | number>
  deptIds?: Array<string | number>
}

export interface PostVO extends BaseEntity {
  postId: string | number
  deptId?: string | number
  deptName?: string
  postCode: string
  postName: string
  postCategory?: string
  postSort: number
  status: string
  remark?: string
}

export interface UserVO extends BaseEntity {
  userId: string | number
  tenantId?: string
  deptId?: number
  deptName?: string
  userName: string
  nickName?: string
  phonenumber?: string
  email?: string
  sex?: string
  status: string
  loginIp?: string
  loginDate?: string
  avatar?: string
  roles?: RoleVO[]
  roleIds?: Array<string | number>
  postIds?: Array<string | number>
}

export interface UserForm {
  userId?: string | number
  deptId?: number | string
  userName: string
  nickName?: string
  password?: string
  phonenumber?: string
  email?: string
  sex?: string
  status: string
  remark?: string
  postIds: Array<string | number>
  roleIds: Array<string | number>
}

export interface UserInfoPayload {
  user: UserVO
  permissions: string[]
  roles: string[]
}

export interface UserEditPayload {
  user?: UserVO
  roles: RoleVO[]
  roleIds: Array<string | number>
  posts: PostVO[]
  postIds: Array<string | number>
}

export interface RoleForm {
  roleId?: string | number
  roleName: string
  roleKey: string
  roleSort: number
  dataScope?: string
  status: string
  remark?: string
  menuCheckStrictly: boolean
  deptCheckStrictly: boolean
  menuIds: Array<string | number>
  deptIds: Array<string | number>
}

export interface RoleDeptPayload {
  checkedKeys: Array<string | number>
  depts: TreeOptionNode[]
}

export interface DeptVO extends BaseEntity {
  deptId: string | number
  deptName: string
  parentId?: string | number
  parentName?: string
  deptCategory?: string
  orderNum?: number
  leader?: string
  phone?: string
  email?: string
  status: string
  children?: DeptVO[]
}

export interface DeptForm {
  deptId?: string | number
  parentId?: string | number
  deptName?: string
  deptCategory?: string
  orderNum?: number
  leader?: string
  phone?: string
  email?: string
  status?: string
}

export interface MenuVO extends BaseEntity {
  menuId: string | number
  menuName: string
  parentId?: string | number
  parentName?: string
  orderNum: number
  path?: string
  component?: string
  queryParam?: string
  isFrame?: string
  isCache?: string
  menuType?: string
  visible?: string
  status?: string
  icon?: string
  remark?: string
  perms?: string
  children?: MenuVO[]
}

export interface MenuForm {
  menuId?: string | number
  parentId?: string | number
  menuName: string
  orderNum: number
  path?: string
  component?: string
  queryParam?: string
  isFrame?: string
  isCache?: string
  menuType?: string
  visible?: string
  status?: string
  icon?: string
  remark?: string
  perms?: string
}

export interface PostForm {
  postId?: string | number
  deptId?: string | number
  postCode: string
  postName: string
  postCategory?: string
  postSort: number
  status: string
  remark?: string
}

export interface TenantVO extends BaseEntity {
  id: string | number
  tenantId: string | number
  username: string
  contactUserName: string
  contactPhone: string
  companyName: string
  licenseNumber?: string
  address?: string
  domain?: string
  intro?: string
  remark?: string
  packageId?: string | number
  expireTime?: string
  accountCount?: number
  status: string
}

export interface TenantForm {
  id?: string | number
  tenantId?: string | number
  username: string
  password?: string
  contactUserName: string
  contactPhone: string
  companyName: string
  licenseNumber?: string
  address?: string
  domain?: string
  intro?: string
  remark?: string
  packageId?: string | number
  expireTime?: string
  accountCount?: number
  status: string
}

export interface TenantPackageVO extends BaseEntity {
  packageId: string | number
  packageName: string
  menuIds?: Array<string | number> | string
  remark?: string
  menuCheckStrictly?: boolean
  status?: string
}

export interface TenantPackageForm {
  packageId?: string | number
  packageName: string
  menuIds: Array<string | number>
  remark?: string
  menuCheckStrictly: boolean
  status?: string
}

export interface MenuTreePayload {
  checkedKeys: Array<string | number>
  menus: TreeOptionNode[]
}

export interface OnlineUserVO extends BaseEntity {
  tokenId: string
  deptName?: string
  userName: string
  ipaddr?: string
  loginLocation?: string
  browser?: string
  os?: string
  loginTime?: string | number
}

export interface OperLogVO extends BaseEntity {
  operId: string | number
  title: string
  businessType: number
  method?: string
  requestMethod?: string
  operName?: string
  deptName?: string
  operUrl?: string
  operIp?: string
  operLocation?: string
  operParam?: string
  jsonResult?: string
  status: number
  errorMsg?: string
  operTime?: string
  costTime?: number
}

export interface LoginLogVO extends BaseEntity {
  infoId: string | number
  userName: string
  status: string
  ipaddr?: string
  loginLocation?: string
  browser?: string
  os?: string
  msg?: string
  loginTime?: string
}

export interface CacheInfoPayload {
  info: Record<string, string>
  dbSize: number
  commandStats: Array<{ name: string; value: string }>
}

export interface CaptchaPayload {
  captchaEnabled: boolean
  uuid?: string
  img?: string
}

export interface TenantListItem {
  tenantId: string
  companyName: string
  domain?: string
}

export interface TenantListPayload {
  tenantEnabled: boolean
  voList: TenantListItem[]
}
