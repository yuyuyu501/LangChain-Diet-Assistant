<template>
  <div class="chat-window" :class="{ 'dark-mode': isDarkMode }">
    <div class="chat-container" :class="{ 'minimized': !isExpanded }">
      <!-- 侧边栏 -->
      <div class="sidebar" :class="{ 'collapsed': isSidebarCollapsed }">
        <!-- 新建会话按钮 -->
        <div class="new-chat">
          <button @click="createSession">
            <span class="icon">+</span>
            <span class="text" v-if="!isSidebarCollapsed">{{ t('chat.newChat') }}</span>
          </button>
        </div>

        <!-- 会话列表 -->
        <div class="session-list">
          <div
            v-for="session in sessions"
            :key="session.session_id"
            :class="['session-item', { active: currentSession?.session_id === session.session_id }]"
            @click="switchSession(session)"
          >
            <span class="session-name">{{ session.session_name }}</span>
            <div class="session-actions">
              <button class="delete-btn" @click.stop="showDeleteConfirm(session)">
                <img :src="Delete" alt="删除" />
              </button>
            </div>
          </div>
        </div>

        <!-- 底部功能区 -->
        <div class="sidebar-footer">
          <button @click="showClearConfirm" class="footer-btn">
            <img :src="isDarkMode ? clearNight : clearDaytime" alt="清空所有会话" />
            <span v-if="!isSidebarCollapsed">{{ t('chat.clearAllSessions') }}</span>
          </button>
          <button @click="toggleDarkMode" class="footer-btn">
            <img :src="isDarkMode ? modelDaytime : modelNight" alt="切换主题" />
            <span v-if="!isSidebarCollapsed">{{ isDarkMode ? t('chat.lightMode') : t('chat.darkMode') }}</span>
          </button>
          <button @click="goToUserCenter" class="footer-btn">
            <img :src="isDarkMode ? personalNight : personalDaytime" alt="个人中心" />
            <span v-if="!isSidebarCollapsed">{{ t('chat.userCenter') }}</span>
          </button>
          <button @click="showLogoutConfirm" class="footer-btn">
            <img :src="isDarkMode ? quitNight : quitDaytime" alt="退出" />
            <span v-if="!isSidebarCollapsed">{{ t('chat.logout') }}</span>
          </button>
        </div>

        <!-- 侧边栏切换按钮 -->
        <button class="sidebar-toggle" @click="toggleSidebar">
          <span>{{ isSidebarCollapsed ? '>' : '<' }}</span>
        </button>
      </div>

      <!-- 主聊天区域 -->
      <div class="main-area">
        <!-- 顶部工具栏 -->
        <div class="toolbar">
          <div class="session-title">{{ currentSession?.session_name || '新对话' }}</div>
          <div class="user-info">
            <img 
              :src="isDarkMode ? settingsNight : settingsDaytime" 
              @click="goToSettings" 
              class="settings-icon" 
              title="设置"
            />
            <el-select v-model="selectedModel" placeholder="选择模型" class="model-select">
              <el-option label="GLM-4-Plus" value="glm-4-plus" />
              <el-option label="Deepseek-R1 1.5B" value="deepseek-r1-1.5b" />
              <el-option label="Qwen2.5 1.5B" value="qwen2.5-1.5b" />
              <el-option label="LLaMA3.2 3B" value="llama3.2-3b" />
              <el-option label="Deepseek-V3 Latest" value="deepseek-v3-latest" />
            </el-select>
            <span class="username">{{ currentUser?.username || '未登录用户' }}</span>
            <SyncManager />
            <img 
              :src="isExpanded ? zoomNight : zoomDaytime" 
              @click="toggleExpand" 
              class="zoom-icon" 
              :title="isExpanded ? '退出全屏' : '全屏'" 
            />
          </div>
        </div>

        <!-- 聊天记录 -->
        <div class="chat-messages" ref="messagesRef">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message', message.role]"
          >
            <div class="avatar" :style="{ backgroundColor: message.role === 'user' ? '#007bff' : '#6c757d' }">
              {{ message.role === 'user' ? (currentUser?.username?.slice(0, 1)?.toUpperCase() || '未') : 'AI' }}
            </div>
            <div class="message-content" :class="{ 'error': message.isError }">
              <!-- 文字内容 -->
              <div v-html="renderMarkdown(message.content)"></div>
              
              <!-- 图片内容 -->
              <div v-if="message.images && message.images.length > 0" class="message-images">
                <div v-for="(image, index) in message.images" 
                     :key="index" 
                     class="message-image-item"
                     @click="() => {
                       expandedImageUrl = `data:image/webp;base64,${image.data}`;
                       expandedImageName = `图片${index + 1}`;
                       showExpandedImage = true;
                     }">
                  <img :src="`data:image/webp;base64,${image.data}`" 
                       alt="聊天图片" 
                       class="message-image"/>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading提示 -->
        <div v-if="isLoading" class="loading-message">
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div class="loading-text">AI正在思考中...</div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <!-- 图片预览区域 -->
          <div v-if="uploadedImages.length > 0" class="image-preview-area">
            <div v-for="(image, index) in uploadedImages" 
                 :key="image.id" 
                 class="image-preview-item">
              <div class="image-preview-container" @click="() => {
                expandedImageUrl = image.url;
                expandedImageName = image.name;
                showExpandedImage = true;
              }">
                <span class="preview-text">{{ image.name.slice(0, 6) }}</span>
              </div>
              <button class="remove-image" @click.stop="removeImage(index)">×</button>
            </div>
          </div>
          
          <!-- 输入框和工具栏容器 -->
          <div class="input-container">
            <div class="input-tools">
              <button class="tool-btn">
                <img :src="Image" alt="图片上传" @click="handleImageUpload" />
              </button>
            </div>
            
            <textarea
              ref="inputRef"
              v-model="inputMessage"
              @input="handleInput"
              @keydown="handleKeyDown"
              :placeholder="t('chat.inputPlaceholder')"
              :style="{ height: textareaHeight + 'px' }"
              :disabled="isLoading"
            ></textarea>
            
            <button class="send-btn" @click="sendMessage" :disabled="isLoading || !inputMessage.trim()">
              <img :src="send" alt="发送" />
            </button>
          </div>
        </div>
        
        <!-- 图片预览弹窗 -->
        <div v-if="showExpandedImage" class="expanded-image-preview" @click="showExpandedImage = false">
          <img :src="expandedImageUrl" :alt="expandedImageName">
          <button class="collapse-btn" @click.stop="showExpandedImage = false">Collapse</button>
        </div>

        <!-- 错误提示 -->
        <div v-if="sendError" class="error-message">
          {{ sendError }}
        </div>
      </div>
    </div>

    <!-- 确认弹窗 -->
    <div v-if="showConfirm" class="confirm-dialog">
      <div class="confirm-content">
        <h3>{{ confirmTitle }}</h3>
        <p>{{ confirmMessage }}</p>
        <div class="confirm-buttons">
          <button @click="handleConfirmCancel" class="cancel-btn">{{ t('chat.confirm.cancel') }}</button>
          <button @click="handleConfirmOk" class="confirm-btn">{{ t('chat.confirm.ok') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storage } from '@/utils/storage'
import { authApi } from '@/api/auth'
import { robotApi } from '@/api/robot'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import SyncManager from '@/components/common/SyncManager.vue'
import { ElSelect, ElOption } from 'element-plus'
import settingsDaytime from '@/components/icons/settings_daytime.png'
import settingsNight from '@/components/icons/settings_night.png'
import { ElMessage } from 'element-plus'

// 导入图标
// import userAvatar from '@/components/icons/user-avatar.png'
// import botAvatar from '@/components/icons/bot-avatar.png'
import Delete from '@/components/icons/Delete.png'
import clearDaytime from '@/components/icons/Clear_all_conversations_daytime.png'
import clearNight from '@/components/icons/Clear_all_conversations_night.png'
import modelDaytime from '@/components/icons/model_daytime.png'
import modelNight from '@/components/icons/model_night.png'
import personalDaytime from '@/components/icons/Personal_Center_daytime.png'
import personalNight from '@/components/icons/Personal_Center_night.png'
import quitDaytime from '@/components/icons/quit_daytime.png'
import quitNight from '@/components/icons/quit_night.png'
import send from '@/components/icons/send.png'
import zoomDaytime from '@/components/icons/zoom_daytime.png'
import zoomNight from '@/components/icons/zoom_night.png'
import Voice from '@/components/icons/Voice.png'
import Image from '@/components/icons/Image.png'

// 状态变量
const router = useRouter()
const isDarkMode = ref(storage.getDarkMode() || false)
const isSidebarCollapsed = ref(false)
const isExpanded = ref(false)
const sessions = ref([])
const currentSession = ref(null)
const messages = ref([])
const inputMessage = ref('')
const messagesRef = ref(null)
const inputRef = ref(null)
const textareaHeight = ref(60) // 初始高度
const showConfirm = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmCallback = ref(null)
const currentUser = ref(null)
const preferences = ref(null)
const isLoading = ref(false)
const sendError = ref(null)

// 新增：图片上传相关的状态
const uploadedImages = ref([])
const imageInput = ref(null)
const expandedImageIndex = ref(-1)

// 在script setup中添加
const showPreview = ref(false)
const previewImageUrl = ref('')
const expandedImageUrl = ref('')
const expandedImageName = ref('')
const showExpandedImage = ref(false)

// 添加模型选择相关的响应式变量
const selectedModel = ref('glm-4-plus')

// 初始化i18n
const { t } = useI18n()

// 监听模型变化
watch(selectedModel, async (newModel) => {
  try {
    // 调用切换模型API
    const switchRes = await robotApi.switchModel(newModel)
    if (!switchRes.success) {
      console.error('切换模型失败:', switchRes.message)
      return
    }

    // 更新用户偏好设置
    const res = await authApi.updateUserPreferences({
      theme: preferences.value?.theme || 'light',
      language: preferences.value?.language || 'zh-CN',
      model: newModel
    })
    
    if (res.success) {
      preferences.value = {
        ...preferences.value,
        model: newModel
      }
    }
  } catch (error) {
    console.error('更新模型设置失败:', error)
  }
})

// 获取用户偏好设置
const fetchUserPreferences = async () => {
  try {
    const res = await authApi.getUserPreferences()
    if (res.success) {
      preferences.value = res.data
      selectedModel.value = res.data.model
      isDarkMode.value = res.data.theme === 'dark'
      storage.setDarkMode(isDarkMode.value)
      document.body.classList.toggle('dark-mode', isDarkMode.value)
    }
  } catch (error) {
    console.error('获取用户偏好设置失败:', error)
  }
}

// 确认弹窗相关
const showDeleteConfirm = (session) => {
  confirmTitle.value = t('chat.confirm.title')
  confirmMessage.value = t('chat.confirm.deleteSession')
  confirmCallback.value = () => deleteSession(session)
  showConfirm.value = true
}

const showClearConfirm = () => {
  confirmTitle.value = t('chat.confirm.title')
  confirmMessage.value = t('chat.confirm.clearAll')
  confirmCallback.value = clearAllSessions
  showConfirm.value = true
}

const showLogoutConfirm = () => {
  confirmTitle.value = t('chat.confirm.title')
  confirmMessage.value = t('chat.confirm.logout')
  confirmCallback.value = logout
  showConfirm.value = true
}

const handleConfirmOk = async () => {
  if (confirmCallback.value) {
    await confirmCallback.value()
  }
  showConfirm.value = false
}

const handleConfirmCancel = () => {
  showConfirm.value = false
}

// 输入框相关
const handleInput = (e) => {
  const textarea = e.target
  // 先将高度设为auto,以便获取实际内容高度
  textarea.style.height = 'auto'
  // 获取内容实际滚动高度
  const scrollHeight = textarea.scrollHeight
  // 限制高度在60px和150px之间
  textareaHeight.value = Math.min(Math.max(scrollHeight, 60), 150)
  textarea.style.height = `${textareaHeight.value}px`
}

const handleKeyDown = (e) => {
  if (e.key === 'Enter') {
    if (e.shiftKey) {
      // Shift+Enter 换行,不需要特殊处理
      return;
    } else {
      // Enter 发送
      e.preventDefault();
      sendMessage();
    }
  }
}

// 工具按钮相关
const handleVoiceInput = () => {
  // TODO: 实现语音输入功能
  console.log('语音输入功能待实现')
}

const handleImageUpload = () => {
  // 检查已上传图片数量
  if (uploadedImages.value.length >= 5) {
    alert('最多只能上传5张图片')
    return
  }
  
  // 创建一个隐藏的文件输入框
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.multiple = true
  
  input.onchange = (e) => {
    const files = Array.from(e.target.files)
    const remainingSlots = 5 - uploadedImages.value.length
    const filesToUpload = files.slice(0, remainingSlots)
    
    filesToUpload.forEach(file => {
      const reader = new FileReader()
      reader.onload = (e) => {
        uploadedImages.value.push({
          id: Date.now() + Math.random(),
          url: e.target.result,
          name: file.name,
          isExpanded: false
        })
      }
      reader.readAsDataURL(file)
    })
  }
  
  input.click()
}

// 修改主题切换方法
const toggleDarkMode = async () => {
  try {
    const newTheme = isDarkMode.value ? 'light' : 'dark'
    const res = await authApi.updateUserPreferences({
      theme: newTheme,
      language: 'zh-CN',
      model: selectedModel.value,
      ai_rules: '',  // 保持现有的AI规则
      is_rules_enabled: false  // 保持现有的规则启用状态
    })
    
    if (res.success) {
      isDarkMode.value = !isDarkMode.value
      storage.setDarkMode(isDarkMode.value)
      document.body.classList.toggle('dark-mode', isDarkMode.value)
    }
  } catch (error) {
    console.error('切换主题失败:', error)
    ElMessage.error('切换主题失败')
  }
}

// 切换展开/缩小状态
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

// 获取会话列表
const fetchSessions = async () => {
  try {
    const res = await authApi.listSessions()
    if (res.success) {
      sessions.value = res.data.sessions
      if (sessions.value.length > 0 && !currentSession.value) {
        switchSession(sessions.value[0])
      }
    }
  } catch (error) {
    console.error('获取会话列表失败:', error)
  }
}

// 创建新会话
const createSession = async () => {
  try {
    const res = await authApi.createSession({
      name: '新对话'
    })
    if (res.success) {
      await fetchSessions()
      switchSession(res.data)
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

// 删除会话
const deleteSession = async (session) => {
  try {
    const res = await authApi.deleteSession(session.session_id)
    if (res.success) {
      // 如果删除的是当前会话，先清空消息列表
      if (currentSession.value?.session_id === session.session_id) {
        messages.value = []
      }
      
      // 删除会话后立即获取最新的会话列表
      const sessionsRes = await authApi.listSessions()
      if (sessionsRes.success) {
        sessions.value = sessionsRes.data.sessions
        
        // 如果没有会话了，等待创建新会话并切换到它
        if (sessions.value.length === 0) {
          const newSessionRes = await authApi.createSession({
            name: '新对话'
          })
          if (newSessionRes.success) {
            // 更新会话列表
            sessions.value = [newSessionRes.data]
            // 切换到新会话
            await switchSession(newSessionRes.data)
          }
        } else if (currentSession.value?.session_id === session.session_id) {
          // 如果删除的是当前会话，切换到第一个会话
          await switchSession(sessions.value[0])
        }
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

// 清空所有会话
const clearAllSessions = async () => {
  try {
    const res = await authApi.clearAllSessions()
    if (res.success) {
      sessions.value = []
      currentSession.value = null
      messages.value = []
      // 清空后创建一个新会话
      await createSession()
    }
  } catch (error) {
    console.error('清空会话失败:', error)
  }
}

// 切换会话
const switchSession = async (session) => {
  currentSession.value = session
  messages.value = []
  try {
    const res = await authApi.getChatHistory(session.session_id)
    if (res.success) {
      messages.value = res.data.messages
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('获取聊天记录失败:', error)
  }
}

// 重置输入框高度
const resetTextareaHeight = () => {
  textareaHeight.value = 60
  if (inputRef.value) {
    inputRef.value.style.height = '60px'
  }
}

// 修改发送消息函数
const sendMessage = async () => {
  if (!inputMessage.value.trim() && uploadedImages.value.length === 0) return;

  const userMessage = {
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date().toISOString(),
    images: uploadedImages.value.map(img => ({
      name: img.name,
      data: img.url.split(',')[1]  // 获取base64数据部分
    }))
  };

  messages.value.push(userMessage);
  inputMessage.value = '';
  uploadedImages.value = [];  // 清空已上传的图片
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom();
  });
  
  isLoading.value = true;
  
  try {
    // 发送消息
    const response = await robotApi.sendMessage(
      currentSession.value.session_id,
      userMessage.content,
      userMessage.images
    );
    
    if (response.success) {
      if (response.message) {
        messages.value.push({
          role: 'assistant',
          content: response.message,
          timestamp: new Date(),
          images: []
        });
        
        // 获取最新消息并更新会话名称
        try {
          // 使用用户的消息作为会话名称
          const newName = userMessage.content.slice(0, 18);
          await updateSessionName(currentSession.value.session_id, newName);
          
          // 更新本地会话列表
          const session = sessions.value.find(s => s.session_id === currentSession.value.session_id);
          if (session) {
            session.session_name = newName;
          }
          // 更新当前会话名称
          if (currentSession.value) {
            currentSession.value.session_name = newName;
          }
        } catch (error) {
          console.error('更新会话名称失败:', error);
        }
      }
      
      // 滚动到底部
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('发送消息失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 添加更新会话名称的函数
const updateSessionName = async (sessionId, newName) => {
  try {
    const res = await authApi.updateSessionName(sessionId, newName)
    if (res.success) {
      // 更新本地会话列表中的名称
      const session = sessions.value.find(s => s.session_id === sessionId)
      if (session) {
        session.session_name = newName
      }
      // 如果是当前会话，也更新currentSession
      if (currentSession.value?.session_id === sessionId) {
        currentSession.value.session_name = newName
      }
    }
  } catch (error) {
    console.error('更新会话名称失败:', error)
  }
}

// 刷新会话列表
const refreshSessions = async () => {
  try {
    const res = await authApi.listSessions()
    if (res.success) {
      sessions.value = res.data.sessions
    }
  } catch (error) {
    console.error('获取会话列表失败:', error)
  }
}

// 刷新用户信息
const refreshUserInfo = async () => {
  try {
    const res = await authApi.getUserInfo()
    if (res.success) {
      currentUser.value = res.data
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 刷新用户统计
const refreshUserStats = async () => {
  try {
    const res = await authApi.getUserStats()
    if (res.success) {
      // userStats.value = res.data
    }
  } catch (error) {
    console.error('获取用户统计失败:', error)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

// 前往个人中心
const goToUserCenter = () => {
  router.push('/user')
}

// 退出登录
const logout = async () => {
  if (!confirm('确定要退出登录吗？')) return
  try {
    await authApi.logout()
  } catch (error) {
    console.error('退出登录失败:', error)
  } finally {
    storage.clearAuth()
    router.push('/auth')
  }
}

// 添加侧边栏收放方法
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    currentUser.value = storage.getUser()
    if (!currentUser.value) {
      const res = await authApi.getUserInfo()
      if (res.success) {
        currentUser.value = res.data
        storage.setUser(res.data)
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 获取用户名首字母
const getUserInitial = (username) => {
  if (!username) return '?'
  return username.charAt(0).toUpperCase()
}

// 添加markdown渲染函数
const renderMarkdown = (content) => {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
}

// 新增：移除图片
const removeImage = (index) => {
  uploadedImages.value.splice(index, 1)
}

// 新增：切换图片展开/折叠状态
const toggleImageExpand = (index) => {
  uploadedImages.value[index].isExpanded = !uploadedImages.value[index].isExpanded
}

// 修改页面加载时的初始化
onMounted(async () => {
  await fetchUserInfo()
  await fetchUserPreferences()
  await fetchSessions()
  await robotApi.getUserRules()
  await authApi.getUserStats()
})

const goToSettings = () => {
  router.push('/settings')
}
</script>

<style scoped>
/* 聊天窗口容器 */
.chat-window {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.chat-window.dark-mode {
  background: #1a1a1a;
}

/* 聊天主容器 */
.chat-container {
  width: 90%;
  height: 90%;
  display: flex;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  margin: 5% auto;
  overflow: hidden; /* 防止子元素溢出 */
}

.chat-container.minimized {
  width: 90%;
  height: 90%;
  margin: 5% auto;
  border-radius: 12px;
}

.chat-container:not(.minimized) {
  height: 100vh;
  width: 100vw;
  margin: 0;
  border-radius: 0;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background-color: #f8f9fa;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  position: relative;
  border-top-left-radius: inherit;
  border-bottom-left-radius: inherit;
}

.dark-mode .sidebar {
  background-color: #333;
  border-right-color: #444;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar.collapsed .new-chat button {
  width: 40px;
  height: 40px;
  padding: 0;
}

.sidebar.collapsed .new-chat button .text {
  display: none;
}

.sidebar.collapsed .session-item .delete-btn {
  width: 0;
  height: 0;
  padding: 0;
  opacity: 0;
}

.sidebar.collapsed .footer-btn span {
  display: none;
}

.sidebar.collapsed .footer-btn {
  justify-content: center;
  padding: 0.5rem;
}

/* 新建会话按钮 */
.new-chat {
  padding: 1rem;
}

.new-chat button {
  width: 100%;
  height: 40px;
  padding: 0 0.8rem;
  background: linear-gradient(90deg, #1a365d 0%, #3B82F6 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.new-chat button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 会话列表 */
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  
  /* 自定义滚动条样式 */
  scrollbar-width: thin;  /* Firefox */
  scrollbar-color: rgba(155, 155, 155, 0.5) transparent;  /* Firefox */
  
  /* Chrome/Safari/Edge 滚动条样式 */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(155, 155, 155, 0.5);
    border-radius: 3px;
    transition: background-color 0.3s;
    
    &:hover {
      background-color: rgba(155, 155, 155, 0.8);
    }
  }
  
  /* 在不滚动时隐藏滚动条 */
  &:not(:hover)::-webkit-scrollbar-thumb {
    background-color: transparent;
  }
}

/* 侧边栏收起时隐藏滚动条 */
.sidebar.collapsed .session-list {
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none;  /* IE and Edge */
  
  &::-webkit-scrollbar {
    display: none;  /* Chrome, Safari, Opera */
  }
}

.dark-mode .session-list {
  /* 暗色模式下的滚动条颜色 */
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;  /* Firefox */
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.3);
    
    &:hover {
      background-color: rgba(255, 255, 255, 0.5);
    }
  }
}

.session-item {
  padding: 0.5rem 0.8rem;
  margin-bottom: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  transition: all 0.3s;
  height: 40px;
}

.session-item span {
  max-width: 150px; /* 限制文字长度 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dark-mode .session-item {
  background-color: #404040;
  color: #fff;
}

.session-item:hover {
  background-color: #f0f0f0;
}

.dark-mode .session-item:hover {
  background-color: #4a4a4a;
}

.session-item.active {
  background-color: #e3f2fd;
  border-left: 3px solid #007bff;
}

.dark-mode .session-item.active {
  background-color: #1a1a1a;
  border-left-color: #0056b3;
}

.session-item .delete-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.session-item .delete-btn:hover {
  opacity: 1;
}

.session-item .delete-btn img {
  width: 20px;
  height: 20px;
}

/* 主聊天区域 */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border-top-right-radius: inherit;
  border-bottom-right-radius: inherit;
}

.dark-mode .main-area {
  background-color: #2d2d2d;
}

/* 工具栏 */
.toolbar {
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dark-mode .toolbar {
  border-bottom-color: #444;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.username {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.dark-mode .username {
  color: #ccc;
}

.avatar {
  flex: 0 0 40px;  /* 固定宽度 */
  width: 40px;     /* 固定宽度 */
  height: 40px;    /* 固定高度 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  margin-right: 1rem;
}

/* 聊天消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  margin: 1rem;
  align-items: flex-start;
  gap: 1rem;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.message-content {
  max-width: 70%;
  padding: 0.8rem 1rem;
  border-radius: 1rem;
  background-color: #f8f9fa;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  word-wrap: break-word;
  overflow-wrap: break-word;
  color: #333;
}

.dark-mode .message-content {
  background-color: #404040;
  color: #e0e0e0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.message.user .message-content {
  background-color: #007bff;
  color: white;
}

.dark-mode .message.user .message-content {
  background-color: #1a365d;
}

/* Markdown样式优化 */
.message-content :deep(p) {
  margin: 0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-content :deep(pre) {
  margin: 0.5rem 0;
  padding: 1rem;
  background-color: #2d2d2d;
  border-radius: 0.5rem;
  overflow-x: auto;
  color: #e0e0e0;
  max-width: 100%;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-all;
}

.dark-mode .message-content :deep(pre) {
  background-color: #1a1a1a;
}

.message-content :deep(code) {
  font-family: 'Courier New', Courier, monospace;
  padding: 0.2rem 0.4rem;
  border-radius: 0.3rem;
  background-color: #f4f4f4;
  color: #333;
}

.dark-mode .message-content :deep(code) {
  background-color: #2d2d2d;
  color: #e0e0e0;
}

.message.user .message-content :deep(code) {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.message-content :deep(ul), 
.message-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message-content :deep(blockquote) {
  margin: 0.5rem 0;
  padding-left: 1rem;
  border-left: 4px solid #ddd;
  color: #666;
}

.dark-mode .message-content :deep(blockquote) {
  border-left-color: #666;
  color: #aaa;
}

.message.user .message-content :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

.message-content :deep(table) {
  margin: 0.5rem 0;
  border-collapse: collapse;
  width: 100%;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 0.5rem;
  border: 1px solid #ddd;
}

.dark-mode .message-content :deep(th),
.dark-mode .message-content :deep(td) {
  border-color: #666;
}

.message.user .message-content :deep(th),
.message.user .message-content :deep(td) {
  border-color: rgba(255, 255, 255, 0.2);
}

.message-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

/* 输入区域 */
.input-area {
  position: relative;
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background-color: #fff;
}

.dark-mode .input-area {
  background-color: #2d2d2d;
  border-top-color: #444;
}

/* 工具栏和输入框容器 */
.input-container {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  width: 100%;
}

/* 图片预览区域 */
.image-preview-area {
  display: flex;
  flex-wrap: wrap;
  margin-left: 50px;
  margin-bottom: 2px;
  padding: 0;
  width: 100%;
  min-height: 32px;
}

.image-preview-item {
  position: relative;
  display: inline-block;
}

.image-preview-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1px 4px;
  background-color: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  height: 24px;
}

.dark-mode .image-preview-container {
  background-color: #404040;
}

.preview-text {
  font-size: 12px;
  color: #666;
}

.dark-mode .preview-text {
  color: #ccc;
}

.remove-image {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: rgba(255, 77, 79, 0.8);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  padding: 0;
  line-height: 1;
}

.expanded-image-preview {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.expanded-image-preview img {
  max-width: 90vw;
  max-height: 80vh;
  object-fit: contain;
}

.collapse-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 6px 12px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.collapse-btn:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

textarea {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  background-color: #fff;
  color: #333;
  overflow-y: auto;
  transition: all 0.3s ease;
  min-height: 60px;
  max-height: 150px;
}

.dark-mode textarea {
  background-color: #404040;
  border-color: #444;
  color: #fff;
}

/* 确认弹窗 */
.confirm-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.confirm-content {
  background-color: #fff;
  padding: 2rem;
  border-radius: 8px;
  width: 300px;
}

.dark-mode .confirm-content {
  background-color: #333;
  color: #fff;
}

.confirm-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.confirm-btn, .cancel-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.confirm-btn {
  background-color: #007bff;
  color: white;
}

.cancel-btn {
  background-color: #e0e0e0;
  color: #333;
}

.dark-mode .cancel-btn {
  background-color: #4a4a4a;
  color: #fff;
}

/* 底部功能区 */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dark-mode .sidebar-footer {
  border-top-color: #444;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border: none;
  background: none;
  color: #666;
  cursor: pointer;
  width: 100%;
  transition: all 0.3s;
}

.dark-mode .footer-btn {
  color: #ccc;
}

.footer-btn:hover {
  background-color: #f0f0f0;
  border-radius: 4px;
}

.dark-mode .footer-btn:hover {
  background-color: #404040;
}

.footer-btn img {
  width: 20px;
  height: 20px;
}

/* 侧边栏切换按钮 */
.sidebar-toggle {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  font-weight: bold;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sidebar-toggle:hover {
  background-color: #0056b3;
}

/* 工具按钮 */
.tool-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.tool-btn:hover {
  opacity: 1;
}

.tool-btn img {
  width: 20px;
  height: 20px;
}

/* 发送按钮 */
.send-btn {
  background: none;
  border: none;
  padding: 0.8rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.send-btn:hover {
  opacity: 1;
}

.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.send-btn img {
  width: 24px;
  height: 24px;
}

.expand-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.expand-btn:hover {
  opacity: 1;
}

.expand-btn img {
  width: 20px;
  height: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.zoom-icon {
  width: 24px;
  height: 24px;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.zoom-icon:hover {
  transform: scale(1.1);
}

/* Loading提示 */
.loading-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 10px 0;
  color: #666;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.dark-mode .loading-message {
  background-color: rgba(45, 45, 45, 0.9);
  color: #ccc;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background-color: #666;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.loading-text {
  margin-top: 8px;
  font-size: 14px;
}

.error-message {
  color: #ff4d4f;
  text-align: center;
  margin: 10px 0;
  padding: 8px;
  background-color: #fff2f0;
  border-radius: 4px;
}

.message-content.error {
  color: #ff4d4f;
  background-color: #fff2f0;
}

/* 添加markdown样式 */


.message-content pre {
  background-color: #f4f4f4;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}

.message-content code {
  background-color: #f4f4f4;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: monospace;
}

.message-content p {
  margin: 0.5rem 0;
}

.message-content ul, .message-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message-content blockquote {
  border-left: 4px solid #ddd;
  margin: 0.5rem 0;
  padding-left: 1rem;
  color: #666;
}

.message-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5rem 0;
}

.message-content th, .message-content td {
  border: 1px solid #ddd;
  padding: 0.5rem;
}

.message-content img {
  max-width: 100%;
  height: auto;
}

/* 新增：图片预览区域样式 */
.image-preview-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  width: 100%;
}

.image-preview-item {
  position: relative;
  display: inline-block;
}

.image-preview-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.dark-mode .image-preview-container {
  background-color: #404040;
}

.preview-text {
  font-size: 14px;
  color: #666;
}

.dark-mode .preview-text {
  color: #ccc;
}

.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #ff4d4f;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  padding: 0;
  line-height: 1;
}

.expanded-image-preview {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.9);
  border-radius: 8px;
  z-index: 1000;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.expanded-image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.image-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.collapse-btn {
  padding: 6px 12px;
  background-color: #666;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.collapse-btn:hover {
  background-color: #555;
}

.message-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  max-width: 100%;
}

.message-image-item {
  position: relative;
  width: 50px;
  height: 50px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.message-image-item:hover {
  transform: scale(1.05);
}

.message-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 图片预览弹窗样式 */
.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.preview-image {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

/* 添加模型选择下拉框样式 */
.model-select {
  margin-right: 1rem;
  width: 120px;
}

.dark-mode .model-select {
  --el-select-bg-color: #1a1a1a;
  --el-select-text-color: #ffffff;
  --el-select-border-color: #444;
}

/* 设置图标样式 */
.settings-icon {
  width: 24px;
  height: 24px;
  cursor: pointer;
  margin: 0 0.5rem;
  transition: transform 0.3s ease;
}

.settings-icon:hover {
  transform: rotate(45deg);
}

/* 统一的滚动条样式 */
.session-list,
.chat-messages {
  /* Firefox */
  scrollbar-width: thin;
  scrollbar-color: rgba(155, 155, 155, 0.5) transparent;
  
  /* Chrome/Safari/Edge */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(155, 155, 155, 0.5);
    border-radius: 3px;
    transition: background-color 0.3s;
    
    &:hover {
      background-color: rgba(155, 155, 155, 0.8);
    }
  }
  
  /* 在不滚动时隐藏滚动条 */
  &:not(:hover)::-webkit-scrollbar-thumb {
    background-color: transparent;
  }
}

/* 暗色模式下的滚动条样式 */
.dark-mode .session-list,
.dark-mode .chat-messages {
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.3);
    
    &:hover {
      background-color: rgba(255, 255, 255, 0.5);
    }
  }
}

/* 修改下拉框暗色模式样式 */
.dark-mode {
  :deep(.el-select-dropdown.el-popper) {
    background-color: #1a1a1a !important;
    border-color: #444 !important;
    
    .el-select-dropdown__item {
      color: #ffffff !important;
      
      &.hover, &:hover {
        background-color: #2d2d2d !important;
      }
      
      &.selected {
        background-color: #333 !important;
        color: #409eff !important;
      }
    }

    .el-scrollbar {
      background-color: #1a1a1a !important;
      
      .el-select-dropdown__list {
        background-color: #1a1a1a !important;
      }
    }

    .el-popper__arrow::before {
      background-color: #1a1a1a !important;
      border-color: #444 !important;
    }
  }

  :deep(.el-select) {
    --el-select-bg-color: #1a1a1a !important;
    --el-select-border-color: #444 !important;
    --el-select-text-color: #ffffff !important;
    --el-select-input-color: #ffffff !important;
    --el-select-option-hover-bg: #2d2d2d !important;
    --el-select-option-selected-bg: #333 !important;
    --el-bg-color: #1a1a1a !important;
    --el-text-color-regular: #ffffff !important;
    --el-border-color: #444 !important;
    --el-fill-color-blank: #1a1a1a !important;

    .el-input__wrapper {
      background-color: #1a1a1a !important;
      box-shadow: 0 0 0 1px #444 !important;
      
      &.is-focus {
        box-shadow: 0 0 0 1px #409eff !important;
      }
      
      input {
        color: #ffffff !important;
        background-color: #1a1a1a !important;
      }
    }
  }
}
</style> 