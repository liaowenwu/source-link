<template>
  <div class="p-2 kaisi-home">
    <el-card shadow="hover" class="mb-[10px] top-card">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-[10px]">
            <span class="font-600">开思工作台</span>
            <el-tag :type="statusTagType(dashboard.serviceStatus)">{{ dashboard.serviceStatus || 'INIT' }}</el-tag>
          </div>
          <div class="flex items-center gap-[8px]">
            <el-button type="primary" :loading="taskLoading" @click="startTask">开启任务</el-button>
            <el-button type="warning" plain :loading="taskLoading" @click="stopTask">停止任务</el-button>
            <el-button type="success" plain :loading="taskLoading" @click="runOnceTask">执行一次</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="12">
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card">
            <div class="metric-label">最近抓取时间</div>
            <div class="metric-value text-[13px]">{{ dashboard.latestCatchTime || '-' }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card">
            <div class="metric-label">今日抓取数</div>
            <div class="metric-value">{{ dashboard.todayCatchCount || 0 }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card">
            <div class="metric-label">今日补价数</div>
            <div class="metric-value">{{ dashboard.todayPriceCount || 0 }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card">
            <div class="metric-label">今日提交数</div>
            <div class="metric-value">{{ dashboard.todaySubmitCount || 0 }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card">
            <div class="metric-label">运行时长(秒)</div>
            <div class="metric-value">{{ dashboard.runningSeconds || 0 }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card clickable" @click="goQuotationTab('WAIT_PRICE_FILL')">
            <div class="metric-label">待补价数量</div>
            <div class="metric-value text-[#e6a23c]">{{ dashboard.waitPriceCount || 0 }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="metric-card clickable" @click="goQuotationTab('WAIT_SUBMIT')">
            <div class="metric-label">待提交数量</div>
            <div class="metric-value text-[#409eff]">{{ dashboard.waitSubmitCount || 0 }}</div>
          </div>
        </el-col>
      </el-row>
      <div class="mt-[10px] text-[13px] text-[#666]">
        <div>接单状态：{{ dashboard.serviceStatus || 'INIT' }}</div>
        <div>当前消息：{{ dashboard.currentMessage || '-' }}</div>
      </div>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :md="12">
        <el-card shadow="hover" class="timeline-card">
          <template #header>
            <div class="font-600">接单动态时间线</div>
          </template>
          <el-timeline class="timeline-body">
            <el-timeline-item
              v-for="item in dashboard.timeline || []"
              :key="`${item.taskNo}-${item.createTime}-${item.displayTitle}`"
              :timestamp="proxy.parseTime(item.createTime)"
              :type="timelineType(item.eventLevel)"
            >
              <div class="font-600">{{ item.displayTitle }}</div>
              <div class="text-[#666]">{{ item.displayContent }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="hover" class="timeline-card">
          <template #header>
            <div class="font-600 text-[#e6a23c]">异常提醒时间线</div>
          </template>
          <el-timeline class="timeline-body">
            <el-timeline-item
              v-for="item in dashboard.alertTimeline || []"
              :key="`${item.quotationId}-${item.createTime}`"
              :timestamp="proxy.parseTime(item.createTime)"
              type="warning"
            >
              <div class="font-600">{{ item.displayTitle }}</div>
              <div class="text-[#666]">{{ item.displayContent }}</div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="!dashboard.alertTimeline || dashboard.alertTimeline.length === 0" description="暂无异常提醒" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="KaisiWorkbenchHome">
import { getKaisiDashboard, runOnceKaisiTask, startKaisiTask, stopKaisiTask } from '@/api/kaisi/workbench';
import { KaisiDashboardVO } from '@/api/kaisi/workbench/types';

const { proxy } = getCurrentInstance() as ComponentInternalInstance;
const router = useRouter();
const dashboard = ref<KaisiDashboardVO>({} as KaisiDashboardVO);
const taskLoading = ref(false);
let timer: number | undefined;

// 定时刷新首页数据，保持状态卡片和时间线实时更新。
const loadDashboard = async () => {
  const { data } = await getKaisiDashboard();
  dashboard.value = data || ({} as KaisiDashboardVO);
};

const startTask = async () => {
  taskLoading.value = true;
  await startKaisiTask();
  proxy?.$modal.msgSuccess('已开启任务');
  taskLoading.value = false;
  await loadDashboard();
};

const stopTask = async () => {
  taskLoading.value = true;
  await stopKaisiTask();
  proxy?.$modal.msgSuccess('已停止任务');
  taskLoading.value = false;
  await loadDashboard();
};

const runOnceTask = async () => {
  taskLoading.value = true;
  await runOnceKaisiTask();
  proxy?.$modal.msgSuccess('已触发执行一次');
  taskLoading.value = false;
  await loadDashboard();
};

const goQuotationTab = (tab: string) => {
  router.push({ path: '/kaisi/quotation', query: { tab } });
};

const statusTagType = (status: string) => {
  if (status === 'RUNNING') return 'success';
  if (status === 'STOPPING' || status === 'STARTING') return 'warning';
  if (status === 'ERROR') return 'danger';
  return 'info';
};

const timelineType = (level: string) => {
  if (level === 'ERROR') return 'danger';
  if (level === 'WARNING') return 'warning';
  if (level === 'SUCCESS') return 'success';
  return 'primary';
};

onMounted(async () => {
  await loadDashboard();
  timer = window.setInterval(loadDashboard, 5000);
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
});
</script>

<style scoped lang="scss">
.kaisi-home {
  .top-card {
    background: linear-gradient(180deg, #fafcff 0%, #ffffff 100%);
  }

  .metric-card {
    border: 1px solid #e8eef7;
    border-radius: 8px;
    padding: 10px 12px;
    background: #fff;
    margin-bottom: 10px;
    min-height: 68px;
  }

  .metric-label {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 4px;
  }

  .metric-value {
    font-size: 22px;
    line-height: 1.2;
    font-weight: 600;
    color: #1f2937;
  }

  .clickable {
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .clickable:hover {
    border-color: #409eff;
    box-shadow: 0 2px 10px rgba(64, 158, 255, 0.12);
  }

  .timeline-card {
    min-height: 560px;
  }

  .timeline-body {
    max-height: 500px;
    overflow: auto;
    padding-right: 8px;
  }
}
</style>
