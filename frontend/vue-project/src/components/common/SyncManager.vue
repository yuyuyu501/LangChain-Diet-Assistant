<template>
  <div v-if="shouldShow" class="sync-manager">
    <!-- 同步状态指示器 -->
    <el-badge :value="unsyncedCount" :hidden="!hasUnsyncedData" type="warning">
      <el-button
        :icon="syncIcon"
        :loading="syncing"
        circle
        @click="handleSyncClick"
      />
    </el-badge>

    <!-- 同步状态对话框 -->
    <el-dialog
      v-model="showSyncDialog"
      :title="t('sync.title')"
      width="30%"
      :close-on-click-modal="false"
    >
      <div class="sync-status">
        <div class="status-item">
          <span>{{ t('sync.lastSyncTime') }}：</span>
          <span>{{ lastSyncTime }}</span>
        </div>
        <div class="status-item">
          <span>{{ t('sync.unsyncedMessages') }}：</span>
          <span>{{ unsyncedData.messages || 0 }}</span>
        </div>
        <div class="status-item">
          <span>{{ t('sync.unsyncedAdvice') }}：</span>
          <span>{{ unsyncedData.advice || 0 }}</span>
        </div>
        <div class="status-item">
          <span>{{ t('sync.unsyncedDietRecords') }}：</span>
          <span>{{ unsyncedData.dietRecords || 0 }}</span>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showSyncDialog = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="syncing" @click="startSync">
            {{ t('sync.startSync') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 冲突解决对话框 -->
    <el-dialog
      v-model="showConflictDialog"
      :title="t('sync.conflict.title')"
      width="50%"
    >
      <div class="conflict-list">
        <div v-for="conflict in conflicts" :key="conflict.id" class="conflict-item">
          <div class="conflict-header">
            <span>{{ getConflictTitle(conflict) }}</span>
          </div>
          <div class="conflict-content">
            <div class="server-data">
              <h4>{{ t('sync.conflict.serverData') }}</h4>
              <pre>{{ formatData(conflict.serverData) }}</pre>
            </div>
            <div class="client-data">
              <h4>{{ t('sync.conflict.clientData') }}</h4>
              <pre>{{ formatData(conflict.clientData) }}</pre>
            </div>
          </div>
          <div class="conflict-actions">
            <el-radio-group v-model="conflict.resolution">
              <el-radio label="keep_server">{{ t('sync.conflict.keepServer') }}</el-radio>
              <el-radio label="keep_client">{{ t('sync.conflict.keepClient') }}</el-radio>
              <el-radio label="merge">{{ t('sync.conflict.merge') }}</el-radio>
            </el-radio-group>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showConflictDialog = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="resolveConflicts">
            {{ t('common.confirm') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { checkSyncStatus, markAsSynced } from '@/api/sync'
import { useLocalStorage } from '@vueuse/core'
import { storage } from '@/utils/storage'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 添加时间转换函数
const formatBeijingTime = (isoTime) => {
  if (!isoTime) return null
  const date = new Date(isoTime)
  // 转换为北京时间
  return date.toLocaleString('zh-CN', { 
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

// 添加路由判断
const route = useRoute()
const isLoginPage = computed(() => route.path === '/auth')
const shouldShow = computed(() => !isLoginPage.value)

// 状态变量
const syncing = ref(false)
const showSyncDialog = ref(false)
const showConflictDialog = ref(false)
const lastSyncTime = ref(null)
const unsyncedData = ref({
  messages: 0,
  advice: 0,
  dietRecords: 0
})
const conflicts = ref([])

// 计算属性
const syncIcon = computed(() => Refresh)
const hasUnsyncedData = computed(() => false)
const unsyncedCount = computed(() => 0)

// 方法
const handleSyncClick = () => {
  showSyncDialog.value = true
}

const checkSync = async () => {
  const token = storage.getToken()
  if (!token) return

  try {
    const { data } = await checkSyncStatus()
    lastSyncTime.value = formatBeijingTime(data.lastSyncAt)
  } catch (error) {
    console.warn('同步状态检查暂时不可用:', error)
    lastSyncTime.value = null
  }
}

const startSync = async () => {
  if (syncing.value) return
  
  syncing.value = true
  try {
    const response = await markAsSynced()
    
    if (response.success) {
      lastSyncTime.value = formatBeijingTime(response.data.lastSyncAt)
      ElMessage.success(t('sync.syncSuccess'))
      showSyncDialog.value = false
      window.location.reload()
    } else {
      ElMessage.error(t('sync.syncFailed'))
    }
  } catch (error) {
    console.error('同步失败:', error)
    ElMessage.error(t('sync.syncFailed'))
  } finally {
    syncing.value = false
  }
}

const resolveConflicts = async () => {
  try {
    await resolveConflict({
      items: conflicts.value.map(conflict => ({
        table: conflict.table,
        record_id: conflict.recordId,
        resolution: conflict.resolution,
        client_data: conflict.clientData,
        server_data: conflict.serverData
      }))
    })
    
    ElMessage.success(t('sync.conflict.resolveSuccess'))
    showConflictDialog.value = false
    await checkSync()
  } catch (error) {
    ElMessage.error(t('sync.conflict.resolveFailed'))
  }
}

const getConflictTitle = (conflict) => {
  const type = t(`sync.types.${conflict.table}`) || t('sync.types.unknown')
  return `${type} - ID: ${conflict.recordId}`
}

const formatData = (data) => {
  return JSON.stringify(data, null, 2)
}

// 修改自动检查的频率
watch(() => storage.getToken(), (newToken) => {
  if (newToken) {
    // 延迟检查，避免立即执行
    setTimeout(checkSync, 1000)
  } else {
    // 清空同步状态
    lastSyncTime.value = null
    unsyncedData.value = {
      messages: 0,
      advice: 0,
      dietRecords: 0
    }
  }
})

// 生命周期钩子
onMounted(async () => {
  // 只在用户已登录时初始化，并添加延迟
  if (storage.getToken()) {
    setTimeout(checkSync, 1000)
  }
})
</script>

<style scoped>
.sync-manager {
  display: inline-flex;
  align-items: center;
}

.sync-status {
  margin-bottom: 20px;
}

.status-item {
  margin: 10px 0;
  display: flex;
  justify-content: space-between;
}

.conflict-list {
  max-height: 400px;
  overflow-y: auto;
}

.conflict-item {
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 15px;
  padding: 15px;
}

.conflict-header {
  margin-bottom: 10px;
  font-weight: bold;
}

.conflict-content {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.server-data,
.client-data {
  flex: 1;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.conflict-actions {
  margin-top: 10px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-size: 12px;
}

:deep(.el-badge__content) {
  z-index: 1;
}

:deep(.el-button) {
  padding: 5px;
  height: 32px;
  width: 32px;
}

:deep(.el-badge) {
  margin-right: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__footer) {
  padding: 20px;
  border-top: 1px solid #eee;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-button) {
  min-width: 80px;
  height: 32px;
  padding: 0 16px;
}

:deep(.el-button.is-circle) {
  width: 32px;
  min-width: unset;
}
</style> 