<template>
  <div class="user-center">
    <!-- 添加快捷访问栏 -->
    <div class="quick-access-bar">
      <el-input
        v-model="searchQuery"
        :placeholder="t('userCenter.quickAccess.search')"
        prefix-icon="Search"
        clearable
        @input="handleSearch"
        class="search-input"
      />
      <div class="quick-shortcuts">
        <el-button
          v-for="shortcut in quickShortcuts"
          :key="shortcut.id"
          :type="shortcut.type"
          :icon="shortcut.icon"
          class="shortcut-button"
          @click="handleShortcutClick(shortcut)"
        >
          {{ t(`userCenter.quickAccess.shortcuts.${shortcut.name}`) }}
        </el-button>
      </div>
    </div>

    <el-container>
      <el-aside width="200px">
        <el-menu
          :default-active="activeMenu"
          class="user-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="profile">
            <el-icon><UserFilled /></el-icon>
            <span>{{ t('userCenter.menu.profile') }}</span>
          </el-menu-item>
          
          <el-menu-item index="health-advice">
            <el-icon><Document /></el-icon>
            <span>{{ t('userCenter.menu.healthAdvice') }}</span>
          </el-menu-item>
          
          <el-menu-item index="dietary-record">
            <el-icon><Calendar /></el-icon>
            <span>{{ t('userCenter.menu.dietaryRecord') }}</span>
          </el-menu-item>
          
          <el-menu-item index="data-analysis">
            <el-icon><TrendCharts /></el-icon>
            <span>{{ t('userCenter.menu.dataAnalysis') }}</span>
          </el-menu-item>
        </el-menu>

        <!-- 返回聊天按钮 -->
        <div class="back-to-chat">
          <el-button 
            type="primary" 
            icon="ChatLineRound" 
            @click="backToChat"
            class="back-button"
          >
            {{ t('userCenter.actions.backToChat') }}
          </el-button>
        </div>
      </el-aside>
      
      <el-main>
        <component 
          :is="currentComponent" 
          v-if="currentComponent"
          @refresh="refreshData"
        />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, shallowRef, onMounted, onUnmounted, watch, markRaw, provide } from 'vue'
import { UserFilled, Document, Calendar, TrendCharts, Search, ChatLineRound } from '@element-plus/icons-vue'
import { useLocalStorage } from '@vueuse/core'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import UserProfile from '@/components/user-center/UserProfile.vue'
import HealthAdvice from '@/components/user-center/HealthAdvice.vue'
import DietaryRecord from '@/components/user-center/DietaryRecord.vue'
import DataAnalysis from '@/components/user-center/DataAnalysis.vue'

const router = useRouter()
const { t } = useI18n()

// 当前激活的菜单项
const activeMenu = ref('profile')

// 当前显示的组件
const currentComponent = shallowRef(UserProfile)

// 组件映射表
const componentMap = {
  'profile': UserProfile,
  'health-advice': HealthAdvice,
  'dietary-record': DietaryRecord,
  'data-analysis': DataAnalysis
}

// 搜索查询
const searchQuery = ref('')

// 快捷方式列表
const quickShortcuts = ref([
  {
    id: 1,
    name: 'latestAdvice',
    icon: Document,
    type: 'primary',
    target: 'health-advice'
  },
  {
    id: 2,
    name: 'todayRecord',
    icon: Calendar,
    type: 'success',
    target: 'dietary-record'
  },
  {
    id: 3,
    name: 'healthReport',
    icon: TrendCharts,
    type: 'warning',
    target: 'data-analysis'
  }
])

// 用户行为记录
const userBehavior = useLocalStorage('user-behavior', {
  visitCounts: {
    profile: 0,
    'health-advice': 0,
    'dietary-record': 0,
    'data-analysis': 0
  },
  lastVisits: {
    profile: null,
    'health-advice': null,
    'dietary-record': null,
    'data-analysis': null
  },
  stayDuration: {
    profile: 0,
    'health-advice': 0,
    'dietary-record': 0,
    'data-analysis': 0
  }
})

// 当前模块的访问开始时间
const moduleStartTime = ref(Date.now())

// 添加 loading 管理
const loading = ref(false)
const loadingText = ref('')

const loadingManager = {
  showLoading: (text = '加载中...') => {
    loading.value = true
    loadingText.value = text
  },
  hideLoading: () => {
    loading.value = false
    loadingText.value = ''
  },
  showProgressBar: (progress, text) => {
    // 可以在这里实现进度条逻辑
  },
  updateProgress: (progress, text) => {
    // 可以在这里实现进度更新逻辑
  },
  showAutoSaveTip: (message, type = 'info') => {
    ElMessage({
      message,
      type,
      duration: 2000
    })
  }
}

// 提供 loadingManager
provide('loadingManager', loadingManager)

// 智能默认视图
const getSmartDefaultView = () => {
  const behavior = userBehavior.value
  let maxScore = 0
  let defaultView = 'profile'

  Object.keys(behavior.visitCounts).forEach(module => {
    // 计算每个模块的综合得分
    const score = behavior.visitCounts[module] * 0.5 + // 访问次数权重
                 behavior.stayDuration[module] * 0.3 + // 停留时间权重
                 (behavior.lastVisits[module] ? 
                   (Date.now() - behavior.lastVisits[module]) * 0.2 : 0) // 最近访问权重

    if (score > maxScore) {
      maxScore = score
      defaultView = module
    }
  })

  return defaultView
}

// 更新访问记录
const updateVisitRecord = (module) => {
  userBehavior.value.visitCounts[module]++
  userBehavior.value.lastVisits[module] = Date.now()
}

// 更新停留时间
const updateStayDuration = (module) => {
  const duration = Date.now() - moduleStartTime.value
  userBehavior.value.stayDuration[module] += duration
  moduleStartTime.value = Date.now()
}

// 监听模块切换
watch(activeMenu, (newModule, oldModule) => {
  if (oldModule) {
    updateStayDuration(oldModule)
  }
  updateVisitRecord(newModule)
  moduleStartTime.value = Date.now()
})

// 处理菜单选择
const handleMenuSelect = (key) => {
  activeMenu.value = key
  currentComponent.value = componentMap[key]
}

// 刷新数据
const refreshData = () => {
  // 触发当前组件的数据刷新
  if (currentComponent.value?.refresh) {
    currentComponent.value.refresh()
  }
}

// 处理搜索
const handleSearch = (query) => {
  // TODO: 实现搜索逻辑
  console.log('搜索:', query)
}

// 处理快捷方式点击
const handleShortcutClick = (shortcut) => {
  activeMenu.value = shortcut.target
  currentComponent.value = componentMap[shortcut.target]
}

// 返回聊天界面
const backToChat = () => {
  router.push('/chat')
}

const icons = {
  document: markRaw(Document),
  calendar: markRaw(Calendar),
  trendCharts: markRaw(TrendCharts)
}

onMounted(() => {
  // 使用智能默认视图
  const defaultView = getSmartDefaultView()
  activeMenu.value = defaultView
  currentComponent.value = componentMap[defaultView]
  
  // 初始化访问记录
  updateVisitRecord(defaultView)
  moduleStartTime.value = Date.now()
  
  // 初始化加载数据
  refreshData()
})

onUnmounted(() => {
  // 保存最后的停留时间
  updateStayDuration(activeMenu.value)
})
</script>

<style scoped>
.user-center {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f5f7fa;
}

.quick-access-bar {
  padding: 16px;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-input {
  width: 300px;
}

.quick-shortcuts {
  display: flex;
  gap: 8px;
}

.shortcut-button {
  min-width: 100px;
}

.el-container {
  flex: 1;
  overflow: hidden;
}

.el-aside {
  background-color: #fff;
  border-right: 1px solid #e6e6e6;
  height: 100%;
  overflow-y: auto;
  position: relative;  /* 添加相对定位 */
  display: flex;      /* 使用flex布局 */
  flex-direction: column; /* 垂直方向排列 */
}

.user-menu {
  border-right: none;
  flex: 1;  /* 菜单占据剩余空间 */
}

.el-main {
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.back-to-chat {
  padding: 16px;
  border-top: 1px solid #e6e6e6;
}

.back-button {
  width: 100%;
}
</style> 