import request from './request'
import { v4 as uuidv4 } from 'uuid'
import { useLocalStorage } from '@vueuse/core'
import { storage } from '@/utils/storage'

// 设备ID存储
const deviceId = useLocalStorage('device_id', uuidv4())

/**
 * 检查数据同步状态
 */
export async function checkSyncStatus() {
  const user = storage.getUser()
  return request({
    url: '/api/sync/status',
    method: 'get',
    params: { device_id: user.device_id }
  })
}

/**
 * 获取未同步的聊天记录
 */
async function getUnsyncedChatRecords() {
  return request({
    url: '/api/chat/unsynced',
    method: 'get',
    params: { device_id: deviceId.value }
  })
}

/**
 * 获取未同步的健康建议
 */
async function getUnsyncedHealthAdvice() {
  return request({
    url: '/api/health-advice/unsynced',
    method: 'get',
    params: { device_id: deviceId.value }
  })
}

/**
 * 获取未同步的饮食记录
 */
async function getUnsyncedDietaryRecords() {
  return request({
    url: '/api/dietary-records/unsynced',
    method: 'get',
    params: { device_id: deviceId.value }
  })
}

/**
 * 获取所有未同步的数据
 */
export async function getUnsyncedData() {
  try {
    const [chatRecords, healthAdvice, dietaryRecords] = await Promise.all([
      getUnsyncedChatRecords(),
      getUnsyncedHealthAdvice(),
      getUnsyncedDietaryRecords()
    ])

    return {
      messages: chatRecords.data || [],
      advice: healthAdvice.data || [],
      dietRecords: dietaryRecords.data || []
    }
  } catch (error) {
    console.error('获取未同步数据失败:', error)
    throw error
  }
}

/**
 * 同步数据
 */
export async function syncData() {
  try {
    // 获取未同步的数据
    const unsyncedData = await getUnsyncedData()
    
    // 发送同步请求
    return request({
      url: '/api/sync/data',
      method: 'post',
      params: { device_id: deviceId.value },
      data: unsyncedData
    })
  } catch (error) {
    console.error('同步数据失败:', error)
    throw error
  }
}

/**
 * 解决数据冲突
 */
export async function resolveConflict(data) {
  return request({
    url: '/api/sync/resolve-conflict',
    method: 'post',
    params: { device_id: deviceId.value },
    data
  })
}

/**
 * 获取设备ID
 */
export function getDeviceId() {
  return deviceId.value
}

/**
 * 更新设备信息
 */
export async function updateDeviceInfo(deviceInfo) {
  return request({
    url: '/api/sync/device',
    method: 'put',
    params: { device_id: deviceId.value },
    data: deviceInfo
  })
}

/**
 * 标记数据为已同步
 */
export async function markAsSynced() {
  const user = storage.getUser()
  return request({
    url: '/api/sync/mark-synced',
    method: 'post',
    params: { device_id: user.device_id }
  })
}

// 注册设备
export const registerDevice = async () => {
  const response = await request({
    url: '/api/devices/register',
    method: 'post'
  })
  if (response.success) {
    // 保存设备ID到本地存储
    storage.setDeviceId(response.data.device_id)
  }
  return response
}

// 获取同步状态
export const getSyncStatus = () => {
  const user = storage.getUser()
  return request({
    url: '/api/sync/status',
    method: 'get',
    params: { device_id: user.device_id }
  })
} 