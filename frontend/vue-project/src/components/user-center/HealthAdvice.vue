<template>
  <div class="health-advice">
    <el-card class="advice-card">
      <template #skeleton>
        <div class="advice-skeleton">
          <el-skeleton style="width: 100%">
            <template #template>
              <el-skeleton-item variant="p" style="width: 100%; height: 40px; margin-bottom: 20px" />
              <div style="display: flex; gap: 20px; margin-bottom: 20px">
                <el-skeleton-item variant="text" style="width: 30%" />
                <el-skeleton-item variant="text" style="width: 30%" />
                <el-skeleton-item variant="text" style="width: 30%" />
              </div>
              <el-skeleton-item variant="p" style="width: 100%; height: 300px" />
            </template>
          </el-skeleton>
        </div>
      </template>

      <template #header>
        <div class="card-header">
          <span>健康建议</span>
          <el-button-group>
            <el-button type="primary" @click="showFavorites">
              <el-icon><Star /></el-icon>收藏夹
            </el-button>
            <el-button type="success" @click="refreshAdvice">
              <el-icon><Refresh /></el-icon>刷新
            </el-button>
          </el-button-group>
        </div>
      </template>

      <!-- 添加高级搜索区域 -->
      <div class="search-area">
        <el-form :model="searchForm" class="search-form">
          <div class="search-row">
            <el-form-item label="关键词">
              <el-input
                v-model="searchForm.keyword"
                placeholder="搜索症状、建议或食材"
                clearable
                @input="handleSearch"
              />
            </el-form-item>
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="searchForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                @change="handleSearch"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">搜索</el-button>
              <el-button @click="resetSearch">重置</el-button>
            </el-form-item>
          </div>
          <div class="tags-row">
            <el-form-item label="标签" class="tags-form-item">
              <el-select
                v-model="searchForm.tags"
                multiple
                placeholder="选择标签"
                @change="handleSearch"
                style="width: 100%"
              >
                <el-option
                  v-for="tag in availableTags"
                  :key="tag.value"
                  :label="tag.label"
                  :value="tag.value"
                />
              </el-select>
            </el-form-item>
          </div>
        </el-form>
      </div>

      <!-- 添加排序选项 -->
      <div class="sort-area">
        <el-radio-group v-model="sortOption" @change="handleSort">
          <el-radio-button value="date">时间</el-radio-button>
          <el-radio-button value="rating">评分</el-radio-button>
        </el-radio-group>
      </div>

      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <el-tab-pane label="最新建议" name="latest">
          <div 
            v-if="activeTab === 'latest'"
            v-infinite-scroll="loadMore"
            :infinite-scroll-disabled="loading || noMore"
            :infinite-scroll-distance="10"
            class="advice-list"
          >
            <div v-if="adviceList.length === 0" class="empty-state">
              <el-empty description="暂无健康建议">
                <el-button type="primary" @click="backToChat">
                  返回聊天获取建议
                </el-button>
              </el-empty>
            </div>
            <div v-else v-for="advice in adviceList" :key="advice.id" class="advice-item">
              <el-card shadow="hover">
                <template #header>
                  <div class="advice-header">
                    <span class="date">{{ formatDate(advice.created_at) }}</span>
                    <div class="actions">
                      <el-rate
                        v-model="advice.rating"
                        @change="(val) => handleRate(advice.id, val)"
                        show-score
                        text-color="#ff9900"
                      />
                      <el-button
                        :type="advice.is_favorite ? 'warning' : 'default'"
                        :icon="Star"
                        circle
                        @click="toggleFavorite(advice.id)"
                      />
                      <el-button
                        type="danger"
                        :icon="Delete"
                        circle
                        @click="handleDelete(advice.id)"
                      />
                    </div>
                  </div>
                </template>
                
                <div class="advice-content">
                  <h4>症状/问题：</h4>
                  <p>{{ advice.symptoms }}</p>
                  
                  <h4>建议内容：</h4>
                  <p>{{ advice.content }}</p>
                  
                  <h4>推荐食材/食谱：</h4>
                  <p>{{ advice.recommended_foods }}</p>
                  
                  <div class="feedback" v-if="advice.rating">
                    <el-input
                      v-model="advice.feedback"
                      type="textarea"
                      placeholder="请输入您的反馈..."
                      :rows="2"
                      @blur="handleFeedback(advice.id, advice.feedback)"
                    />
                  </div>
                </div>
              </el-card>
            </div>
            
            <div v-if="loading" class="loading-more">
              <el-skeleton :rows="1" animated />
            </div>
            
            <!-- <div v-if="noMore" class="no-more">
              没有更多数据了
            </div> -->
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="收藏夹" name="favorites">
          <div v-if="activeTab === 'favorites'" class="advice-list">
            <div v-if="favoritesList.length === 0" class="empty-state">
              <el-empty description="暂无收藏的建议">
                <el-button type="primary" @click="backToChat">
                  返回聊天获取建议
                </el-button>
              </el-empty>
            </div>
            <div v-else v-for="advice in favoritesList" :key="advice.id" class="advice-item">
              <el-card shadow="hover">
                <template #header>
                  <div class="advice-header">
                    <span class="date">{{ formatDate(advice.created_at) }}</span>
                    <div class="actions">
                      <el-rate
                        v-model="advice.rating"
                        @change="(val) => handleRate(advice.id, val)"
                        show-score
                        text-color="#ff9900"
                      />
                      <el-button
                        type="warning"
                        :icon="Star"
                        circle
                        @click="toggleFavorite(advice.id)"
                      />
                      <el-button
                        type="danger"
                        :icon="Delete"
                        circle
                        @click="handleDelete(advice.id)"
                      />
                    </div>
                  </div>
                </template>
                
                <div class="advice-content">
                  <h4>症状/问题：</h4>
                  <p>{{ advice.symptoms }}</p>
                  
                  <h4>建议内容：</h4>
                  <p>{{ advice.content }}</p>
                  
                  <h4>推荐食材/食谱：</h4>
                  <p>{{ advice.recommended_foods }}</p>
                  
                  <div class="feedback" v-if="advice.rating">
                    <el-input
                      v-model="advice.feedback"
                      type="textarea"
                      placeholder="请输入您的反馈..."
                      :rows="2"
                      @blur="handleFeedback(advice.id, advice.feedback)"
                    />
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, onActivated, onDeactivated } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star, Refresh, Delete } from '@element-plus/icons-vue'
import { 
  getHealthAdvices,
  getFavoriteAdvices,
  updateAdviceRating,
  toggleAdviceFavorite,
  updateAdviceFeedback,
  deleteHealthAdvice
} from '@/api/health-advice'
import { useRouter } from 'vue-router'

const router = useRouter()
const loadingManager = inject('loadingManager')
const activeTab = ref('latest')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const adviceList = ref([])
const favoritesList = ref([])
const loading = ref(false)
const noMore = ref(false)

// 缓存相关
const CACHE_KEY = 'health-advice-cache'
const CACHE_EXPIRY = 5 * 60 * 1000 // 5分钟缓存

// 搜索表单
const searchForm = ref({
  keyword: '',
  dateRange: [],
  tags: []
})

// 排序选项
const sortOption = ref('date')

// 可用标签 - 这里可以从后端获取或根据数据动态生成
const availableTags = ref([
  { value: 'diet', label: '饮食建议' },
  { value: 'exercise', label: '运动建议' },
  { value: 'sleep', label: '睡眠建议' },
  { value: 'seasonal', label: '季节性建议' },
  { value: 'chronic', label: '慢性病管理' }
])

// 格式化日期
const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

// 预加载下一页数据
const preloadNextPage = async () => {
  try {
    const nextPage = currentPage.value + 1
    const { items } = await getHealthAdvices({
      page: nextPage,
      page_size: pageSize.value,
      ...buildSearchParams()
    })
    if (items.length > 0) {
      loadingManager.cacheData(`${CACHE_KEY}-${nextPage}`, items)
    }
  } catch (error) {
    console.error('预加载失败:', error)
  }
}

// 构建搜索参数
const buildSearchParams = () => {
  return {
    keyword: searchForm.value.keyword,
    start_date: searchForm.value.dateRange?.[0],
    end_date: searchForm.value.dateRange?.[1],
    tags: searchForm.value.tags,
    sort: sortOption.value
  }
}

// 获取健康建议列表
const fetchAdviceList = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    loadingManager.showLoading('正在加载健康建议...')
    const response = await getHealthAdvices({
      page: currentPage.value,
      page_size: pageSize.value,
      ...buildSearchParams()
    })
    
    if (response.success) {
      const processItems = (items) => items.map(item => ({
        ...item,
        rating: Number(item.rating) || 0 // 确保rating是数字类型
      }));

      if (currentPage.value === 1) {
        adviceList.value = processItems(response.data.items);
      } else {
        adviceList.value = [...adviceList.value, ...processItems(response.data.items)];
      }
      noMore.value = response.data.items.length < pageSize.value;
    }
  } catch (error) {
    console.error('获取健康建议失败:', error)
    ElMessage.error('获取健康建议失败')
  } finally {
    loading.value = false
    loadingManager.hideLoading()
  }
}

// 加载更多数据
const loadMore = async () => {
  if (loading.value || noMore.value) return
  
  currentPage.value++
  await fetchAdviceList()
}

// 处理评分
const handleRate = async (adviceId, rating) => {
  loadingManager.showProgressBar(0, '正在保存评分...')
  try {
    loadingManager.updateProgress(50, '更新评分...')
    await updateAdviceRating(adviceId, rating)
    loadingManager.updateProgress(100, '评分成功')
    loadingManager.showAutoSaveTip('评分已保存', 'success')
  } catch (error) {
    loadingManager.showAutoSaveTip('评分保存失败', 'error')
  }
}

// 切换收藏状态
const toggleFavorite = async (adviceId) => {
  loadingManager.showProgressBar(0, '正在更新收藏状态...')
  try {
    loadingManager.updateProgress(30, '更新状态...')
    await toggleAdviceFavorite(adviceId)
    loadingManager.updateProgress(60, '刷新列表...')
    // 刷新两个列表
    await Promise.all([fetchAdviceList(), fetchFavoritesList()])
    loadingManager.updateProgress(100, '操作完成')
    loadingManager.showAutoSaveTip('收藏状态已更新', 'success')
  } catch (error) {
    loadingManager.showAutoSaveTip('操作失败', 'error')
  }
}

// 处理反馈
const handleFeedback = async (adviceId, feedback) => {
  loadingManager.showProgressBar(0, '正在保存反馈...')
  try {
    loadingManager.updateProgress(50, '保存反馈...')
    await updateAdviceFeedback(adviceId, feedback)
    loadingManager.updateProgress(100, '保存完成')
    loadingManager.showAutoSaveTip('反馈已保存', 'success')
  } catch (error) {
    loadingManager.showAutoSaveTip('保存反馈失败', 'error')
  }
}

// 显示收藏夹
const showFavorites = () => {
  activeTab.value = 'favorites'
  loadingManager.showAutoSaveTip('切换到收藏夹', 'info')
}

// 刷新建议
const refreshAdvice = () => {
  loadingManager.showAutoSaveTip('正在刷新数据...', 'info')
  if (activeTab.value === 'latest') {
    fetchAdviceList()
  } else {
    fetchFavoritesList()
  }
}

// 处理标签页切换
const handleTabClick = async () => {
  // 重置状态
  currentPage.value = 1
  noMore.value = false
  loading.value = false
  
  // 清空列表数据
  if (activeTab.value === 'latest') {
    adviceList.value = []
    await fetchAdviceList()
  } else {
    favoritesList.value = []
    await fetchFavoritesList()
  }
}

// 处理搜索
const handleSearch = async () => {
  currentPage.value = 1
  noMore.value = false
  adviceList.value = []
  await fetchAdviceList()
}

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    keyword: '',
    dateRange: [],
    tags: []
  }
  sortOption.value = 'date'
  loadingManager.showAutoSaveTip('已重置搜索条件', 'info')
  handleSearch()
}

// 处理排序
const handleSort = () => {
  handleSearch()
}

// 获取收藏列表
const fetchFavoritesList = async () => {
  if (loading.value) return;
  
  loading.value = true;
  loadingManager.showLoading('正在加载收藏列表...');
  try {
    // 从本地存储或者状态管理中获取user_id
    const userInfo = JSON.parse(localStorage.getItem('user'));
    const userId = userInfo.user_id;
    
    const response = await getFavoriteAdvices({
      user_id: userId,  // 添加user_id参数
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchForm.value.keyword,
      sort: sortOption.value,
      start_date: searchForm.value.dateRange?.[0],
      end_date: searchForm.value.dateRange?.[1]
    });
    if (response.success) {
      favoritesList.value = response.data.items;
      total.value = response.data.total;
      noMore.value = response.data.items.length < pageSize.value;
    }
    loadingManager.showAutoSaveTip('加载完成', 'success');
  } catch (error) {
    loadingManager.showAutoSaveTip('获取收藏列表失败', 'error');
  } finally {
    loading.value = false;
    loadingManager.hideLoading();
  }
}

// 组件激活时（keep-alive）
onActivated(() => {
  // 检查缓存是否过期
  const cachedData = loadingManager.getCachedData(CACHE_KEY, CACHE_EXPIRY)
  if (!cachedData) {
    fetchAdviceList(false)
  }
})

// 组件失活时（keep-alive）
onDeactivated(() => {
  // 可以在这里做一些清理工作
})

// 组件挂载时获取数据
onMounted(() => {
  fetchAdviceList();
  fetchFavoritesList();
})

// 暴露刷新方法给父组件
defineExpose({
  refresh: refreshAdvice
})

// 返回聊天界面
const backToChat = () => {
  router.push('/chat')
}

// 处理删除
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条健康建议吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loadingManager.showProgressBar(0, '正在删除...')
    const response = await deleteHealthAdvice(id)
    
    if (response.success) {
      loadingManager.updateProgress(100, '删除成功')
      loadingManager.showAutoSaveTip('建议已删除', 'success')
      // 刷新列表
      if (activeTab.value === 'latest') {
        await fetchAdviceList()
      } else {
        await fetchFavoritesList()
      }
    } else {
      throw new Error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      loadingManager.showAutoSaveTip('删除失败', 'error')
      console.error('删除健康建议失败:', error)
    }
  }
}
</script>

<style scoped>
.health-advice {
  max-width: 800px;
  margin: 0 auto;
}

.advice-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.advice-item {
  margin-bottom: 20px;
}

.advice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date {
  color: #909399;
  font-size: 14px;
}

.advice-content {
  h4 {
    margin: 10px 0;
    color: #303133;
  }
  
  p {
    margin: 0 0 15px;
    color: #606266;
    line-height: 1.6;
  }
}

.feedback {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.empty-state :deep(.el-empty__description) {
  margin-top: 20px;
  font-size: 16px;
  color: #909399;
}

.empty-state :deep(.el-button) {
  margin-top: 20px;
}

.advice-list {
  min-height: 200px;
  padding: 20px;
  position: relative;
  width: 100%;
}

.el-tabs :deep(.el-tabs__content) {
  overflow: visible;
  position: relative;
}

.el-tabs :deep(.el-tab-pane) {
  position: relative;
  width: 100%;
}

.search-area {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.search-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-start;
}

.tags-row {
  width: 100%;
}

.tags-form-item {
  width: 100%;
  margin-bottom: 0;
}

.tags-form-item :deep(.el-form-item__content) {
  width: 100%;
}

.sort-area {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.advice-skeleton {
  padding: 20px;
}

.loading-more {
  padding: 20px;
  text-align: center;
}

.no-more {
  padding: 20px;
  text-align: center;
  color: #909399;
}
</style> 