import request from './request'
import CacheManager from '@/utils/cache'

/**
 * 获取数据分析统计信息
 * @param {Object} params - 查询参数
 * @param {number} [params.days] - 天数
 * @param {string} [params.start_date] - 开始日期
 * @param {string} [params.end_date] - 结束日期
 */
export const getAnalysisStatistics = (params) => {
  return request({
    url: '/api/analysis/statistics',
    method: 'get',
    params
  })
}

/**
 * 获取评分分布分析
 * @param {Object} params - 查询参数
 * @param {number} [params.days] - 天数
 */
export const getRatingAnalysis = (params) => {
  return request({
    url: '/api/analysis/rating',
    method: 'get',
    params
  })
}

/**
 * 获取用户反馈类型分析
 * @param {Object} params - 查询参数
 * @param {number} [params.days] - 天数
 */
export const getFeedbackAnalysis = (params) => {
  return request({
    url: '/api/analysis/feedback',
    method: 'get',
    params
  })
}

/**
 * 获取建议效果分析
 * @param {Object} params - 查询参数
 * @param {number} params.days - 分析天数
 */
export async function getBMI(params) {
  const cacheKey = `effectiveness_${params.days}`
  const cachedData = CacheManager.getCache('analysisData', cacheKey)
  
  if (cachedData) {
    return cachedData
  }

  const data = await request({
    url: '/api/analysis/bmi',
    method: 'get',
    params
  })

  CacheManager.setCache('analysisData', cacheKey, data)
  return data
}

/**
 * 获取AI模型分析
 * @param {Object} params - 查询参数
 * @param {number} params.days - 分析天数
 */
export async function getModelAnalysis(params) {
  const cacheKey = `model_${params.days}`
  const cachedData = CacheManager.getCache('analysisData', cacheKey)
  
  if (cachedData) {
    return cachedData
  }

  const data = await request({
    url: '/api/analysis/model',
    method: 'get',
    params
  })

  CacheManager.setCache('analysisData', cacheKey, data)
  return data
}

/**
 * 清除分析数据缓存
 */
export function clearAnalysisCache() {
  CacheManager.clearCache('analysisData')
} 