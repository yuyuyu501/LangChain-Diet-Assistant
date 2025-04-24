import { useLocalStorage } from '@vueuse/core'

// 缓存配置
const CACHE_CONFIG = {
  userProfile: {
    key: 'user_profile_cache',
    maxAge: 1800000 // 30分钟
  },
  healthAdvice: {
    key: 'health_advice_cache',
    maxAge: 300000 // 5分钟
  },
  dietaryRecord: {
    key: 'dietary_record_cache',
    maxAge: 300000 // 5分钟
  },
  analysisData: {
    key: 'analysis_data_cache',
    maxAge: 1800000 // 30分钟
  }
}

// 缓存存储
const cacheStorage = useLocalStorage('app_cache', {})

/**
 * 缓存管理器
 */
class CacheManager {
  /**
   * 设置缓存
   * @param {string} type - 缓存类型
   * @param {string} key - 缓存键
   * @param {any} data - 缓存数据
   */
  static setCache(type, key, data) {
    if (!CACHE_CONFIG[type]) {
      throw new Error(`未知的缓存类型: ${type}`)
    }

    const cacheKey = `${CACHE_CONFIG[type].key}_${key}`
    cacheStorage.value[cacheKey] = {
      data,
      timestamp: Date.now()
    }
  }

  /**
   * 获取缓存
   * @param {string} type - 缓存类型
   * @param {string} key - 缓存键
   * @returns {any|null} 缓存数据或null
   */
  static getCache(type, key) {
    if (!CACHE_CONFIG[type]) {
      throw new Error(`未知的缓存类型: ${type}`)
    }

    const cacheKey = `${CACHE_CONFIG[type].key}_${key}`
    const cached = cacheStorage.value[cacheKey]

    if (cached && Date.now() - cached.timestamp < CACHE_CONFIG[type].maxAge) {
      return cached.data
    }

    return null
  }

  /**
   * 清除指定类型的缓存
   * @param {string} type - 缓存类型
   * @param {string} [key] - 可选的缓存键
   */
  static clearCache(type, key) {
    if (!CACHE_CONFIG[type]) {
      throw new Error(`未知的缓存类型: ${type}`)
    }

    if (key) {
      const cacheKey = `${CACHE_CONFIG[type].key}_${key}`
      delete cacheStorage.value[cacheKey]
    } else {
      // 清除该类型的所有缓存
      const prefix = CACHE_CONFIG[type].key
      Object.keys(cacheStorage.value).forEach(key => {
        if (key.startsWith(prefix)) {
          delete cacheStorage.value[key]
        }
      })
    }
  }

  /**
   * 清除所有缓存
   */
  static clearAllCache() {
    cacheStorage.value = {}
  }

  /**
   * 清除过期缓存
   */
  static clearExpiredCache() {
    Object.entries(cacheStorage.value).forEach(([key, value]) => {
      const type = Object.keys(CACHE_CONFIG).find(t => key.startsWith(CACHE_CONFIG[t].key))
      if (type && Date.now() - value.timestamp >= CACHE_CONFIG[type].maxAge) {
        delete cacheStorage.value[key]
      }
    })
  }
}

// 定期清理过期缓存
setInterval(() => {
  CacheManager.clearExpiredCache()
}, 300000) // 每5分钟清理一次

export default CacheManager 