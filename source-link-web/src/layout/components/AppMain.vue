<template>
  <section class="app-main">
    <router-view v-slot="{ Component, route }">
      <transition :enter-active-class="animate" mode="out-in">
        <keep-alive :include="tagsViewStore.cachedViews">
          <component :is="Component" v-if="!route.meta.link" :key="route.path" />
        </keep-alive>
      </transition>
    </router-view>
    <iframe-toggle />
  </section>
</template>

<script setup name="AppMain" lang="ts">
import { useSettingsStore } from '@/store/modules/settings';
import { useTagsViewStore } from '@/store/modules/tagsView';

import IframeToggle from './IframeToggle/index.vue';
const { proxy } = getCurrentInstance() as ComponentInternalInstance;
const route = useRoute();
const tagsViewStore = useTagsViewStore();

// 随机动画集合
const animate = ref<string>('');
const animationEnable = ref(useSettingsStore().animationEnable);
watch(
  () => useSettingsStore().animationEnable,
  (val: boolean) => {
    animationEnable.value = val;
    if (val) {
      animate.value = proxy?.animate.animateList[Math.round(Math.random() * proxy?.animate.animateList.length)] as string;
    } else {
      animate.value = proxy?.animate.defaultAnimate as string;
    }
  },
  { immediate: true }
);

onMounted(() => {
  addIframe();
});

watchEffect(() => {
  addIframe();
});

function addIframe() {
  if (route.meta.link) {
    useTagsViewStore().addIframeView(route);
  }
}
</script>

<style lang="scss" scoped>
.app-main {
  min-height: calc(100vh - 74px);
  width: 100%;
  position: relative;
  overflow: hidden;
}

.fixed-header + .app-main {
  padding-top: 62px;
}

.hasTagsView {
  .app-main {
    min-height: calc(100vh - 108px);
  }

  .fixed-header + .app-main {
    padding-top: 96px;
  }
}
</style>
<style lang="scss">
// fix css style bug in open el-dialog
.el-popup-parent--hidden {
  .fixed-header {
    padding-right: 6px;
  }
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background-color: var(--el-fill-color-lighter);
}

::-webkit-scrollbar-thumb {
  background-color: var(--el-text-color-placeholder);
  border-radius: 999px;
}
</style>
