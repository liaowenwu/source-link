<template>
  <div class="home-wrap">
    <section class="hero-grid">
      <article class="hero-main">
        <p class="hero-kicker">Source Link Workspace</p>
        <h1>系统管理与租户管理工作台</h1>
        <p class="hero-desc">聚焦用户、角色、菜单、租户、套餐与参数维护，减少层级跳转，常用入口集中在一屏完成。</p>
        <div class="hero-actions">
          <el-button type="primary" @click="go('/system/user')">进入用户管理</el-button>
          <el-button plain @click="go('/system/tenant')">进入租户管理</el-button>
        </div>
      </article>

      <aside class="hero-aside">
        <h3>快捷操作</h3>
        <button class="quick-item" @click="go('/system/role')">
          <span>角色权限配置</span>
          <el-tag size="small" type="primary" effect="plain">Role</el-tag>
        </button>
        <button class="quick-item" @click="go('/system/menu')">
          <span>菜单与按钮权限</span>
          <el-tag size="small" type="success" effect="plain">Menu</el-tag>
        </button>
        <button class="quick-item" @click="go('/system/tenantPackage')">
          <span>租户套餐维护</span>
          <el-tag size="small" type="warning" effect="plain">Package</el-tag>
        </button>
        <button class="quick-item" @click="go('/system/config')">
          <span>系统参数配置</span>
          <el-tag size="small" type="info" effect="plain">Config</el-tag>
        </button>
      </aside>
    </section>

    <section class="module-grid">
      <button class="module-card" @click="go('/system/user')">
        <svg-icon icon-class="user" />
        <h3>用户管理</h3>
        <p>用户账号、部门、岗位与状态维护。</p>
      </button>
      <button class="module-card" @click="go('/system/role')">
        <svg-icon icon-class="peoples" />
        <h3>角色管理</h3>
        <p>角色权限分配与数据范围配置。</p>
      </button>
      <button class="module-card" @click="go('/system/menu')">
        <svg-icon icon-class="tree" />
        <h3>菜单管理</h3>
        <p>前端路由、菜单树和按钮权限。</p>
      </button>
      <button class="module-card" @click="go('/system/tenant')">
        <svg-icon icon-class="company" />
        <h3>租户管理</h3>
        <p>租户信息、状态与到期时间管理。</p>
      </button>
      <button class="module-card" @click="go('/system/tenantPackage')">
        <svg-icon icon-class="category" />
        <h3>租户套餐</h3>
        <p>套餐菜单分配和授权范围维护。</p>
      </button>
      <button class="module-card" @click="go('/system/dict')">
        <svg-icon icon-class="dict" />
        <h3>字典管理</h3>
        <p>字典类型和字典数据统一维护。</p>
      </button>
    </section>
  </div>
</template>

<script setup lang="ts" name="Index">
const router = useRouter();

const go = (path: string) => {
  router.push(path);
};
</script>

<style lang="scss" scoped>
.home-wrap {
  min-height: calc(100vh - 136px);
  padding: 8px;
  background:
    radial-gradient(circle at 8% 10%, rgba(37, 99, 235, 0.09), transparent 32%),
    radial-gradient(circle at 88% 0%, rgba(14, 165, 233, 0.1), transparent 28%),
    var(--el-bg-color-page);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.65fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}

.hero-main {
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 58%, #0891b2 100%);
  color: #eef4ff;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 16px 32px rgba(29, 78, 216, 0.22);

  h1 {
    margin: 8px 0 12px;
    font-size: clamp(24px, 2vw, 34px);
    line-height: 1.2;
  }

  .hero-kicker {
    margin: 0;
    font-size: 12px;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    opacity: 0.88;
  }

  .hero-desc {
    margin: 0;
    max-width: 620px;
    color: rgba(238, 244, 255, 0.9);
    line-height: 1.7;
  }

  .hero-actions {
    margin-top: 18px;
    display: flex;
    gap: 10px;

    :deep(.el-button--primary) {
      --el-button-text-color: #1e3a8a;
      --el-button-bg-color: #ffffff;
      --el-button-border-color: #ffffff;
      --el-button-hover-bg-color: #eff6ff;
      --el-button-hover-border-color: #eff6ff;
    }

    :deep(.el-button.is-plain) {
      --el-button-text-color: #ffffff;
      --el-button-border-color: rgba(255, 255, 255, 0.6);
      --el-button-bg-color: rgba(255, 255, 255, 0.08);
      --el-button-hover-bg-color: rgba(255, 255, 255, 0.16);
      --el-button-hover-border-color: rgba(255, 255, 255, 0.85);
    }
  }
}

.hero-aside {
  border-radius: 18px;
  padding: 18px;
  border: 1px solid #dce6f3;
  background: #ffffff;

  h3 {
    margin: 4px 0 12px;
    font-size: 16px;
    color: #0f172a;
  }
}

.quick-item {
  width: 100%;
  border: 1px solid #e4eaf2;
  background: #ffffff;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  color: #334155;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;

  &:last-child {
    margin-bottom: 0;
  }

  &:hover {
    border-color: #93c5fd;
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(37, 99, 235, 0.12);
  }
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.module-card {
  border: 1px solid #dce6f3;
  background: #ffffff;
  border-radius: 16px;
  text-align: left;
  padding: 18px;
  cursor: pointer;
  transition: all 0.2s ease;

  .svg-icon {
    font-size: 24px;
    color: #1d4ed8;
    margin-bottom: 8px;
  }

  h3 {
    margin: 0;
    font-size: 17px;
    color: #0f172a;
  }

  p {
    margin: 8px 0 0;
    font-size: 13px;
    line-height: 1.6;
    color: #64748b;
  }

  &:hover {
    transform: translateY(-2px);
    border-color: #93c5fd;
    box-shadow: 0 12px 26px rgba(37, 99, 235, 0.14);
  }
}

@media (max-width: 1200px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .module-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .home-wrap {
    padding: 4px;
  }

  .hero-main {
    padding: 20px;
  }

  .module-grid {
    grid-template-columns: 1fr;
  }
}
</style>
