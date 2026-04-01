<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NCard, NForm, NFormItem, NInput, NSelect, NSpin } from 'naive-ui'
import { getCaptcha, getTenantList } from '@/api/modules/auth'
import { useAuthStore } from '@/stores/auth'
import { message } from '@/utils/discrete'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const captchaLoading = ref(false)
const captchaImage = ref('')
const tenantEnabled = ref(false)
const tenantOptions = ref<Array<{ label: string; value: string }>>([])

const form = reactive({
  username: 'admin',
  password: 'admin123',
  tenantId: '',
  code: '',
  uuid: '',
})

const rules = {
  username: { required: true, message: '请输入用户名', trigger: ['blur', 'input'] },
  password: { required: true, message: '请输入密码', trigger: ['blur', 'input'] },
  code: { required: true, message: '请输入验证码', trigger: ['blur', 'input'] },
}

const redirect = computed(() => String(route.query.redirect || '/overview'))

async function loadCaptcha() {
  captchaLoading.value = true
  try {
    const result = await getCaptcha()
    form.uuid = result.data.uuid || ''
    captchaImage.value = result.data.img ? `data:image/png;base64,${result.data.img}` : ''
  } catch {
    captchaImage.value = ''
    message.error('验证码加载失败，请检查后端服务与 Redis 状态')
  } finally {
    captchaLoading.value = false
  }
}

async function loadTenants() {
  try {
    const result = await getTenantList()
    tenantEnabled.value = result.data.tenantEnabled
    tenantOptions.value = result.data.voList.map((item) => ({
      label: item.companyName,
      value: item.tenantId,
    }))
    if (tenantEnabled.value && !form.tenantId && tenantOptions.value.length > 0) {
      form.tenantId = tenantOptions.value[0].value
    }
  } catch {
    tenantEnabled.value = false
  }
}

async function handleSubmit() {
  loading.value = true
  try {
    await authStore.login({
      username: form.username,
      password: form.password,
      tenantId: form.tenantId || undefined,
      code: form.code,
      uuid: form.uuid,
    })
    message.success('登录成功，欢迎回来')
    await router.replace(redirect.value)
  } finally {
    loading.value = false
    form.code = ''
    await loadCaptcha()
  }
}

onMounted(async () => {
  await Promise.all([loadCaptcha(), loadTenants()])
})
</script>

<template>
  <div class="login-page min-h-screen">
    <div class="login-overlay" />
    <div class="login-noise" />

    <main class="relative z-10 flex min-h-screen items-center justify-center px-6 py-10">
      <NCard
        class="login-card w-full max-w-[460px] rounded-[28px] border-none shadow-[0_28px_80px_rgba(16,32,42,0.22)]"
        content-style="padding: 30px;"
      >
        <div class="space-y-6">
          <div class="space-y-2">
            <p class="text-xs uppercase tracking-[0.28em] text-[color:var(--text-muted)]">Source Link</p>
            <h1 class="text-3xl font-semibold tracking-tight text-[color:var(--text-main)]">欢迎登录</h1>
            <p class="text-sm leading-6 text-[color:var(--text-secondary)]">请输入账号信息以访问系统控制台。</p>
          </div>

          <NForm :model="form" :rules="rules" label-placement="top">
            <NFormItem label="用户名" path="username">
              <NInput v-model:value="form.username" placeholder="请输入用户名" />
            </NFormItem>

            <NFormItem label="密码" path="password">
              <NInput v-model:value="form.password" type="password" show-password-on="click" placeholder="请输入密码" />
            </NFormItem>

            <NFormItem v-if="tenantEnabled" label="租户" path="tenantId">
              <NSelect v-model:value="form.tenantId" :options="tenantOptions" placeholder="请选择租户" />
            </NFormItem>

            <NFormItem label="验证码" path="code">
              <div class="grid w-full grid-cols-[1fr_140px] gap-3">
                <NInput v-model:value="form.code" placeholder="请输入验证码" />
                <button
                  type="button"
                  class="overflow-hidden rounded-2xl border border-[color:var(--panel-border)] bg-[#f7f1e7]"
                  @click="loadCaptcha"
                >
                  <NSpin :show="captchaLoading">
                    <img v-if="captchaImage" :src="captchaImage" alt="captcha" class="h-11 w-full object-cover" />
                    <span v-else class="block px-4 py-3 text-sm text-[color:var(--text-secondary)]">点击刷新</span>
                  </NSpin>
                </button>
              </div>
            </NFormItem>

            <NButton type="primary" block size="large" :loading="loading" @click="handleSubmit">
              登录系统
            </NButton>
          </NForm>
        </div>
      </NCard>
    </main>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 16%, rgba(86, 170, 180, 0.35), transparent 42%),
    radial-gradient(circle at 83% 78%, rgba(240, 177, 94, 0.3), transparent 36%),
    linear-gradient(135deg, #0e1f2b 0%, #163244 42%, #20485f 100%);
}

.login-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: radial-gradient(circle at center, black 45%, transparent 100%);
  opacity: 0.4;
}

.login-noise {
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(circle, rgba(255, 255, 255, 0.1) 0 1px, transparent 1px) 0 0 / 8px 8px,
    radial-gradient(circle at 30% 60%, rgba(255, 255, 255, 0.08), transparent 60%),
    radial-gradient(circle at 65% 35%, rgba(255, 255, 255, 0.08), transparent 62%);
  mix-blend-mode: soft-light;
  opacity: 0.35;
}

.login-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 249, 240, 0.93);
}
</style>
