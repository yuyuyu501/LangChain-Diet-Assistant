<template>
  <div class="data-analysis">
    <el-card class="analysis-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('dataAnalysis.title') }}</span>
          <el-button-group>
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>{{ t('dataAnalysis.buttons.refresh') }}
            </el-button>
            <el-button type="success" @click="exportData">
              <el-icon><Download /></el-icon>{{ t('dataAnalysis.buttons.export') }}
            </el-button>
          </el-button-group>
        </div>
      </template>

      <!-- 时间范围选择 -->
      <div class="time-range">
        <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
          <el-radio-button value="7">{{ t('dataAnalysis.timeRange.last7Days') }}</el-radio-button>
          <el-radio-button value="30">{{ t('dataAnalysis.timeRange.last30Days') }}</el-radio-button>
          <el-radio-button value="90">{{ t('dataAnalysis.timeRange.last90Days') }}</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 数据概览 -->
      <el-row :gutter="20" class="data-overview">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <div class="overview-header">
                <span>{{ t('dataAnalysis.overview.totalAdvices') }}</span>
                <el-tooltip content="系统生成的健康建议总数">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </template>
            <div class="overview-content">
              <span class="number">{{ statistics.totalAdvices || 0 }}</span>
              <span class="trend" :class="{ up: statistics.adviceIncrease > 0 }">
                {{ statistics.adviceIncrease || 0 }}%
                <el-icon><CaretTop /></el-icon>
              </span>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <div class="overview-header">
                <span>{{ t('dataAnalysis.overview.averageRating') }}</span>
                <el-tooltip content="用户对建议的平均评分">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </template>
            <div class="overview-content">
              <span class="number">{{ statistics.averageRating || 0 }}</span>
              <el-rate
                v-model="statistics.averageRating"
                disabled
                show-score
                text-color="#ff9900"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 反馈分析 -->
      <div class="analysis-section">
        <h3>{{ t('dataAnalysis.userFeedback') }}</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-container">
              <h4>{{ t('dataAnalysis.ratingDistribution') }}</h4>
              <div ref="ratingDistributionChart" style="height: 300px"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <h4>{{ t('dataAnalysis.feedbackTypeDistribution') }}</h4>
              <div ref="feedbackTypeChart" style="height: 300px"></div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 效果分析 -->
      <div class="analysis-section">
        <h3>{{ t('dataAnalysis.userAnalysis') }}</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-container">
              <h4>{{ t('dataAnalysis.bmiIndex') }}</h4>
              <div ref="symptomTrendChart" style="height: 300px"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <h4>{{ t('dataAnalysis.adviceEffectComparison') }}</h4>
              <div ref="adviceTypeChart" style="height: 300px"></div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, Download, InfoFilled, CaretTop
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { 
  getAnalysisStatistics,
  getRatingAnalysis,
  getFeedbackAnalysis,
  getBMI,
  clearAnalysisCache
} from '@/api/data-analysis'
import { useI18n } from 'vue-i18n'

const loadingManager = inject('loadingManager', {
  showLoading: () => {},
  hideLoading: () => {},
  showProgressBar: () => {},
  updateProgress: () => {},
  showAutoSaveTip: () => {}
})

const { t } = useI18n()

// 图表实例
const ratingDistributionChart = ref(null)
const feedbackTypeChart = ref(null)
const symptomTrendChart = ref(null)
const adviceTypeChart = ref(null)

// 时间范围
const timeRange = ref('30')

// 统计数据
const statistics = ref({
  totalAdvices: 0,
  adviceIncrease: 0,
  averageRating: 0
})

// 初始化图表
const initCharts = () => {
  // 评分分布图表
  const ratingChart = echarts.init(ratingDistributionChart.value)
  ratingChart.setOption({
    title: { text: t('dataAnalysis.ratingDistribution') },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['1分', '2分', '3分', '4分', '5分'] },
    yAxis: { type: 'value' },
    series: [{
      data: [0, 0, 0, 0, 0],
      type: 'bar',
      showBackground: true,
      backgroundStyle: {
        color: 'rgba(180, 180, 180, 0.2)'
      }
    }]
  })

  // 反馈类型分布图表
  const feedbackChart = echarts.init(feedbackTypeChart.value)
  feedbackChart.setOption({
    title: { text: t('dataAnalysis.feedbackTypeDistribution') },
    tooltip: { trigger: 'item' },
    legend: { 
      orient: 'horizontal',
      bottom: 0,
      right: 0
    },
    series: [{
      type: 'pie',
      radius: '50%',
      data: [
        { value: 0, name: '效果显著' },
        { value: 0, name: '部分改善' },
        { value: 0, name: '效果一般' },
        { value: 0, name: '无明显效果' }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  })

  // 症状改善趋势图表
  const symptomChart = echarts.init(symptomTrendChart.value)
  const today = new Date();
  const dateLabels = Array.from({length: 30}, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    return `${date.getMonth() + 1}月${date.getDate()}日`;
  }).reverse();
  symptomChart.setOption({
    title: { text: t('dataAnalysis.bmiIndex') },
    tooltip: { trigger: 'axis' },
    xAxis: { 
      type: 'category', 
      data: dateLabels
    },
    yAxis: { type: 'value' },
    series: [{
      data: Array.from({length: 30}, () => Math.floor(Math.random() * (30) + 15)),
      type: 'line',
      smooth: true
    }]
  })

  // 建议类型效果对比图表
  const adviceChart = echarts.init(adviceTypeChart.value)
  adviceChart.setOption({
    title: { text: t('dataAnalysis.adviceEffectComparison') },
    tooltip: { trigger: 'axis' },
    legend: { data: ['改善率', '满意度'] },
    xAxis: { type: 'category', data: ['饮食建议', '运动建议', '作息建议', '综合建议'] },
    yAxis: { type: 'value' },
    series: [
      {
        name: '改善率',
        type: 'bar',
        data: [85, 75, 80, 90]
      },
      {
        name: '满意度',
        type: 'bar',
        data: [90, 80, 85, 95]
      }
    ]
  })

  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    ratingChart.resize()
    feedbackChart.resize()
    symptomChart.resize()
    adviceChart.resize()
  })
}

// 获取统计数据
const fetchStatistics = async () => {
  loadingManager.showLoading('正在加载统计数据...')
  try {
    const response = await getAnalysisStatistics(getTimeRange())
    if (response.success) {
      statistics.value = response.data
      loadingManager.showAutoSaveTip('统计数据加载完成', 'success')
    } else {
      loadingManager.showAutoSaveTip('加载统计数据失败', 'error')
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    loadingManager.showAutoSaveTip('加载统计数据失败', 'error')
  } finally {
    loadingManager.hideLoading()
  }
}

// 获取时间范围
const getTimeRange = () => {
  return { days: parseInt(timeRange.value) }
}

// 处理时间范围变化
const handleTimeRangeChange = () => {
  refreshData()
}

// 刷新数据
const refreshData = async () => {
  loadingManager.showLoading('正在加载统计数据...')
  try {
    await fetchRatingAnalysis();
    await fetchFeedbackAnalysis();
    await fetchBMI();
    const response = await getAnalysisStatistics(getTimeRange())
    if (response.success) {
      statistics.value = response.data
      loadingManager.showAutoSaveTip('统计数据加载完成', 'success')
    } else {
      loadingManager.showAutoSaveTip('加载统计数据失败', 'error')
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    loadingManager.showAutoSaveTip('加载统计数据失败', 'error')
  } finally {
    loadingManager.hideLoading()
  }
}

// 添加新的获取数据函数
const fetchRatingAnalysis = async () => {
  try {
    const data = await getRatingAnalysis({ days: parseInt(timeRange.value) })
    console.log('获取评分分析数据:', data); 
    // 更新评分分布图表数据
    updateRatingChart(data)
  } catch (error) {
    console.error('获取评分分析数据失败:', error)
  }
}

const fetchFeedbackAnalysis = async () => {
  try {
    const data = await getFeedbackAnalysis({ days: parseInt(timeRange.value) })
    // 更新反馈类型图表数据
    updateFeedbackChart(data)
  } catch (error) {
    console.error('获取反馈分析数据失败:', error)
  }
}

const fetchBMI = async () => {
  try {
    const data = await getBMI({ days: parseInt(timeRange.value) });
    // 更新BMI指数图表数据
    updateEffectivenessCharts(data);
  } catch (error) {
    console.error('获取BMI数据失败:', error);
  }
}

// 添加图表更新函数
const updateRatingChart = (data) => {
  const ratingChart = echarts.getInstanceByDom(ratingDistributionChart.value)
  
  if (ratingChart && data.data && data.data.ratingDistribution) {
    console.log('更新评分分布图表数据:', data.data.ratingDistribution); 
    ratingChart.setOption({
      series: [{
        data: data.data.ratingDistribution
      }]
    })
  }
}

const updateFeedbackChart = (data) => {
  const feedbackChart = echarts.getInstanceByDom(feedbackTypeChart.value)
  
  if (feedbackChart && data.data) {
    const feedbackData = [
      { value: data.data['效果显著'], name: '效果显著' },
      { value: data.data['部分改善'], name: '部分改善' },
      { value: data.data['效果一般'], name: '效果一般' },
      { value: data.data['无明显效果'], name: '无明显效果' }
    ]
    feedbackChart.setOption({
      series: [{
        data: feedbackData
      }]
    })
  }
}

const updateEffectivenessCharts = (data) => {
  const symptomChart = echarts.getInstanceByDom(symptomTrendChart.value);
  if (symptomChart && data.data) {
    const bmiValues = data.data.map(item => item.bmi_value);
    const dates = data.data.map(item => item.date);
    symptomChart.setOption({
      xAxis: {
        data: dates
      },
      series: [{
        data: bmiValues
      }]
    });
  }
}

// 导出数据
const exportData = () => {
  loadingManager.showAutoSaveTip('正在准备导出数据...', 'info')
  // TODO: 实现数据导出功能
}

// 组件挂载时初始化
onMounted(() => {
  initCharts()
  refreshData()  // 使用 refreshData 替代 fetchStatistics，这样会同时获取所有数据
})

// 暴露刷新方法给父组件
defineExpose({
  refresh: refreshData
})
</script>

<style scoped>
.data-analysis {
  max-width: 1200px;
  margin: 0 auto;
}

.analysis-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-range {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
}

.data-overview {
  margin-bottom: 30px;
}

.overview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-icon {
    color: #909399;
    cursor: help;
  }
}

.overview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  
  .number {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
  }
  
  .trend {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #f56c6c;
    
    &.up {
      color: #67c23a;
    }
  }
}

.analysis-section {
  margin-top: 30px;
  
  h3 {
    margin-bottom: 20px;
    padding-left: 10px;
    border-left: 4px solid #409eff;
  }
  
  h4 {
    margin-bottom: 15px;
    color: #606266;
  }
}

.chart-container {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}
</style> 