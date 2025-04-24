<template>
  <div class="settings-container" :class="{ 'dark-mode': isDarkMode }">
    <div class="container">
      <!-- 顶部导航 -->
      <div class="top-nav">
        <button class="back-btn" @click="goBack">
          <span>←</span> {{ t('common.back') }}
        </button>
        <h1>{{ t('settings.title') }}</h1>
        <div></div>
      </div>

      <!-- 仪表盘区域 -->
      <div class="dashboard-section">
        <h2>{{ t('dashboard.title') }}</h2>
        <div class="stats-grid">
          <div class="stat-card" 
               @mousemove="handleMouseMove"
               @mouseleave="handleMouseLeave"
               ref="statCards">
            <h3>{{ t('dashboard.totalSessions') }}</h3>
            <p>{{ stats.total_sessions || 0 }}</p>
          </div>
          <div class="stat-card"
               @mousemove="handleMouseMove"
               @mouseleave="handleMouseLeave"
               ref="statCards">
            <h3>{{ t('dashboard.totalMessages') }}</h3>
            <p>{{ stats.total_conversations || 0 }}</p>
          </div>
          <div class="stat-card"
               @mousemove="handleMouseMove"
               @mouseleave="handleMouseLeave"
               ref="statCards">
            <h3>{{ t('dashboard.totalTokens') }}</h3>
            <p>{{ stats.total_tokens || 0 }}</p>
          </div>
          <div class="stat-card"
               @mousemove="handleMouseMove"
               @mouseleave="handleMouseLeave"
               ref="statCards">
            <h3>{{ t('dashboard.lastActive') }}</h3>
            <p>{{ formatDate(stats.last_active_at) }}</p>
          </div>
        </div>
      </div>

      <!-- 用户偏好设置区域 -->
      <div class="settings-section">
        <h2>{{ t('settings.title') }}</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label>{{ t('settings.theme.label') }}</label>
            <select v-model="theme" @change="updatePreferences">
              <option value="light">{{ t('settings.theme.light') }}</option>
              <option value="dark">{{ t('settings.theme.dark') }}</option>
            </select>
          </div>
          <div class="setting-item">
            <label>{{ t('settings.language.label') }}</label>
            <select v-model="language" @change="updatePreferences">
              <option value="zh-CN">{{ t('settings.language.zhCN') }}</option>
              <option value="en-US">{{ t('settings.language.enUS') }}</option>
            </select>
          </div>
          <div class="setting-item">
            <label>{{ t('settings.model.label') }}</label>
            <select v-model="selectedModel" @change="updatePreferences">
              <option value="glm-4-plus">{{ t('settings.model.glm') }}</option>
              <option value="deepseek-r1-1.5b">{{ t('settings.model.deepseek') }}</option>
              <option value="qwen2.5-1.5b">{{ t('settings.model.qwen') }}</option>
              <option value="llama3.2-3b">{{ t('settings.model.llama') }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- AI个性化规则设置区域 -->
      <div class="settings-section">
        <h2>{{ t('settings.aiRules.label') }}</h2>
        <div class="ai-rules-grid">
          <div class="rule-card">
            <div class="rule-header">
              <h3>{{ t('settings.aiRules.label') }}</h3>
              <label class="switch">
                <input type="checkbox" v-model="isRuleEnabled">
                <span class="slider"></span>
              </label>
            </div>
            <div class="rule-content">
              <textarea
                v-model="aiRules"
                :placeholder="t('settings.aiRules.placeholder')"
                rows="6"
                class="rule-textarea"
                @input="handleRulesChange"
                :disabled="!isRuleEnabled"
              ></textarea>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storage } from '@/utils/storage'
import { authApi } from '@/api/auth'
import { robotApi } from '@/api/robot'
import { debounce } from 'lodash'
import { ElMessage } from 'element-plus'

const { t, locale } = useI18n()
const router = useRouter()
const isDarkMode = ref(storage.getDarkMode() || false)
const theme = ref('light')
const language = ref(storage.getLanguage())
const selectedModel = ref('glm-4-plus')
const currentModel = ref('glm-4-plus')
const stats = ref({
  total_sessions: 0,
  total_conversations: 0,
  total_tokens: 0,
  last_active_at: null
})

const statCards = ref([])
const aiRules = ref('')
const isRuleEnabled = ref(false)
const loading = ref(false)

// 获取用户偏好设置
const fetchPreferences = async () => {
  try {
    loading.value = true
    const res = await authApi.getUserPreferences()
    if (res.success) {
      theme.value = res.data.theme
      language.value = res.data.language
      selectedModel.value = res.data.model
      isDarkMode.value = res.data.theme === 'dark'
      storage.setDarkMode(isDarkMode.value)
      document.body.classList.toggle('dark-mode', isDarkMode.value)
      aiRules.value = res.data.ai_rules || ''
      isRuleEnabled.value = res.data.is_rules_enabled || false
      
      // 更新语言
      locale.value = res.data.language
      storage.setLanguage(res.data.language)
    }
  } catch (error) {
    console.error('获取用户偏好设置失败:', error)
    ElMessage.error(t('errors.networkError'))
  } finally {
    loading.value = false
  }
}

// 获取用户统计信息
const fetchUserStats = async () => {
  try {
    const res = await authApi.getUserStats()
    if (res.success) {
      stats.value = res.data
    }
  } catch (error) {
    console.error('获取用户统计信息失败:', error)
  }
}

// 更新用户偏好设置
const updatePreferences = debounce(async () => {
  try {
    // 如果是模型变更，先调用切换模型API
    if (selectedModel.value !== currentModel.value) {
      const switchRes = await robotApi.switchModel(selectedModel.value)
      if (!switchRes.success) {
        ElMessage.error(t('errors.serverError'))
        return
      }
      currentModel.value = selectedModel.value
    }

    const response = await authApi.updateUserPreferences({
      theme: theme.value,
      language: language.value,
      model: selectedModel.value,
      ai_rules: aiRules.value,
      is_rules_enabled: isRuleEnabled.value
    })

    if (response.success) {
      // 更新主题
      isDarkMode.value = theme.value === 'dark'
      storage.setDarkMode(isDarkMode.value)
      document.body.classList.toggle('dark-mode', isDarkMode.value)
      
      // 更新语言
      locale.value = language.value
      storage.setLanguage(language.value)
    }
  } catch (error) {
    console.error('更新偏好设置失败:', error)
    ElMessage.error(t('errors.networkError'))
  }
}, 500)

// 格式化日期
const formatDate = (date) => {
  if (!date) return t('dashboard.neverActive')
  return new Date(date).toLocaleString(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 处理鼠标移动事件
const handleMouseMove = (e) => {
  const card = e.currentTarget
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  // 计算倾斜角度
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const angleX = (y - centerY) / 10
  const angleY = -(x - centerX) / 10
  
  // 应用变换
  card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) scale3d(1.05, 1.05, 1.05)`
}

// 处理鼠标离开事件
const handleMouseLeave = (e) => {
  const card = e.currentTarget
  card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)'
}

// 更新用户偏好设置
const handleRulesChange = debounce(async () => {
  try {
    const res = await authApi.updateUserPreferences({
      theme: theme.value,
      language: language.value,
      model: selectedModel.value,
      ai_rules: aiRules.value,
      is_rules_enabled: isRuleEnabled.value
    })
    if (res.success) {
      // 移除频繁的成功提示
      // ElMessage.success('设置已保存')
    }
  } catch (error) {
    console.error('更新偏好设置失败:', error)
    ElMessage.error(t('errors.networkError'))
  }
}, 500)

// 监听规则开关变化
watch(isRuleEnabled, (newValue) => {
  handleRulesChange()
})

// 监听主题变化
watch(() => theme.value, (newTheme) => {
  updatePreferences()
})

onMounted(() => {
  fetchPreferences()
  fetchUserStats()
})
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  height: 100vh;
  background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%);
  display: flex;
}

.settings-container.dark-mode {
  background: #1a1a1a;
}

.container {
  flex: 1;
  background: white;
  padding: 2rem;
  margin: 0;
  max-width: none;
  border-radius: 0;
  box-shadow: none;
  overflow-y: auto;
}

.dark-mode .container {
  background: #2d2d2d;
  color: #fff;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  color: #666;
  cursor: pointer;
  font-size: 1rem;
}

.dark-mode .back-btn {
  color: #ccc;
}

.back-btn:hover {
  color: #333;
}

.dark-mode .back-btn:hover {
  color: #fff;
}

h1 {
  padding-right:100px;
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.dark-mode h1 {
  color: #fff;
}

.dashboard-section,
.settings-section {
  background: #edf0f2;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.dark-mode .dashboard-section,
.dark-mode .settings-section {
  background: #404040;
}

h2 {
  margin: 0 0 1.5rem;
  color: #333;
  font-size: 1.2rem;
}

.dark-mode h2 {
  color: #fff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease-out;
  transform-style: preserve-3d;
  will-change: transform;
  transform: perspective(1000px) rotateX(0) rotateY(0);
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.stat-card h3 {
  margin: 0;
  color: #4a5568;
  font-size: 1.1rem;
  font-weight: normal;
  margin-bottom: 1rem;
}

.stat-card p {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
  color: #2d3748;
  line-height: 1.2;
}

.dark-mode .stat-card {
  background: #2d2d2d;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.dark-mode .stat-card h3 {
  color: #ccc;
}

.dark-mode .stat-card p {
  color: #fff;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-item label {
  color: #4a5568;
  font-size: 0.9rem;
}

.dark-mode .setting-item label {
  color: #ccc;
}

select {
  padding: 0.5rem;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  background: #f8f9fa;
  color: #2d3748;
}

.dark-mode select {
  background: #2d2d2d;
  border-color: #444;
  color: #fff;
}

.ai-rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.rule-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.dark-mode .rule-card {
  background: #2d2d2d;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #3B82F6;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.rule-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rule-textarea {
  width: 100%;
  min-height: 120px;
  padding: 0.75rem;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 0.9rem;
  resize: vertical;
  margin-bottom: 1rem;
}

.dark-mode .rule-textarea {
  border-color: #4a5568;
  background: #2d3748;
  color: #e2e8f0;
}

.rule-textarea:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.rule-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style> 