<template>
  <div class="loading-manager">
    <!-- 骨架屏 -->
    <div v-if="showSkeleton" class="skeleton-container">
      <slot name="skeleton">
        <div class="default-skeleton">
          <el-skeleton :rows="3" animated />
        </div>
      </slot>
    </div>

    <!-- 全局加载动画 -->
    <div v-if="loading" class="global-loading">
      <el-loading
        :fullscreen="true"
        :text="loadingText"
        background="rgba(255, 255, 255, 0.8)"
      />
    </div>

    <!-- 进度条 -->
    <el-progress
      v-if="showProgress"
      :percentage="progress"
      :status="progressStatus"
      :text="progressText"
      class="progress-bar"
    />

    <!-- 自动保存提示 -->
    <div v-if="showAutoSave" class="auto-save-tip">
      <el-alert
        :title="autoSaveText"
        :type="autoSaveStatus"
        show-icon
        :closable="false"
      />
    </div>

    <!-- 重试提示 -->
    <el-dialog
      v-model="showRetryDialog"
      title="加载失败"
      width="30%"
    >
      <span>{{ retryMessage }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleRetryCancel">取消</el-button>
          <el-button type="primary" @click="handleRetry">
            重试
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 操作撤销提示 -->
    <el-dialog
      v-model="showUndoDialog"
      title="操作提示"
      width="30%"
      :show-close="false"
      :close-on-click-modal="false"
    >
      <span>{{ undoMessage }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleUndoCancel">取消</el-button>
          <el-button type="primary" @click="handleUndoConfirm">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import { ElMessage } from 'element-plus'
import { useLocalStorage } from '@vueuse/core'

// 加载状态
const loading = ref(false)
const loadingText = ref('加载中...')

// 骨架屏状态
const showSkeleton = ref(false)

// 进度条状态
const showProgress = ref(false)
const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('')

// 自动保存状态
const showAutoSave = ref(false)
const autoSaveText = ref('')
const autoSaveStatus = ref('info')

// 重试对话框状态
const showRetryDialog = ref(false)
const retryMessage = ref('')
const retryCount = ref(0)
const maxRetries = 3
const retryCallback = ref(null)

// 撤销对话框状态
const showUndoDialog = ref(false)
const undoMessage = ref('')
const undoCallback = ref(null)
const undoCancelCallback = ref(null)

// 离线缓存
const offlineCache = useLocalStorage('offline-cache', {})

// 显示骨架屏
const showSkeletonScreen = () => {
  showSkeleton.value = true
}

// 隐藏骨架屏
const hideSkeletonScreen = () => {
  showSkeleton.value = false
}

// 显示加载
const showLoading = (text = '加载中...') => {
  loading.value = true
  loadingText.value = text
}

// 隐藏加载
const hideLoading = () => {
  loading.value = false
}

// 显示进度条
const showProgressBar = (initialProgress = 0, text = '') => {
  showProgress.value = true
  progress.value = initialProgress
  progressText.value = text
  progressStatus.value = 'primary'
}

// 更新进度
const updateProgress = (newProgress, text = '') => {
  progress.value = newProgress
  if (text) progressText.value = text
  if (newProgress >= 100) {
    progressStatus.value = 'success'
    setTimeout(() => {
      showProgress.value = false
    }, 1000)
  }
}

// 显示自动保存提示
const showAutoSaveTip = (text = '正在保存...', status = 'info') => {
  showAutoSave.value = true
  autoSaveText.value = text
  autoSaveStatus.value = status
  if (status !== 'warning') {
    setTimeout(() => {
      showAutoSave.value = false
    }, 3000)
  }
}

// 显示重试对话框
const showRetry = async (message, callback) => {
  if (retryCount.value < maxRetries) {
    retryMessage.value = message
    retryCallback.value = callback
    showRetryDialog.value = true
  } else {
    ElMessage.error('已达到最大重试次数，请稍后再试')
    retryCount.value = 0
  }
}

// 处理重试
const handleRetry = async () => {
  showRetryDialog.value = false
  retryCount.value++
  if (retryCallback.value) {
    try {
      await retryCallback.value()
      retryCount.value = 0
    } catch (error) {
      showRetry(retryMessage.value, retryCallback.value)
    }
  }
}

// 处理重试取消
const handleRetryCancel = () => {
  showRetryDialog.value = false
  retryCount.value = 0
}

// 缓存数据
const cacheData = (key, data) => {
  offlineCache.value[key] = {
    data,
    timestamp: Date.now()
  }
}

// 获取缓存数据
const getCachedData = (key, maxAge = 3600000) => {
  const cached = offlineCache.value[key]
  if (cached && Date.now() - cached.timestamp < maxAge) {
    return cached.data
  }
  return null
}

// 清除缓存
const clearCache = (key) => {
  if (key) {
    delete offlineCache.value[key]
  } else {
    offlineCache.value = {}
  }
}

// 显示操作撤销对话框
const showUndo = (message, confirmCallback, cancelCallback = null) => {
  undoMessage.value = message
  undoCallback.value = confirmCallback
  undoCancelCallback.value = cancelCallback
  showUndoDialog.value = true
}

// 处理撤销确认
const handleUndoConfirm = () => {
  if (undoCallback.value) {
    undoCallback.value()
  }
  showUndoDialog.value = false
}

// 处理撤销取消
const handleUndoCancel = () => {
  if (undoCancelCallback.value) {
    undoCancelCallback.value()
  }
  showUndoDialog.value = false
}

// 提供给其他组件使用的方法
provide('loadingManager', {
  showLoading,
  hideLoading,
  showProgressBar,
  updateProgress,
  showAutoSaveTip,
  showUndo,
  showSkeletonScreen,
  hideSkeletonScreen,
  showRetry,
  cacheData,
  getCachedData,
  clearCache
})
</script>

<style scoped>
.loading-manager {
  position: fixed;
  z-index: 9999;
}

.skeleton-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #fff;
  z-index: 9996;
}

.default-skeleton {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9998;
}

.auto-save-tip {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9997;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 