import request from './request'
import { storage } from '@/utils/storage'

// 获取用户名
export const getUsername = (userId) => {
  return request({
    url: `/api/users/${userId}`,
    method: 'get'
  })
}

// 获取用户资料
export const getUserProfile = (userId) => {
  return request({
    url: `/api/user_profiles/${userId}`,
    method: 'get'
  })
}

// 更新用户资料
export const updateUserProfile = (userId, data) => {
  return request({
    url: `/api/user_profiles/${userId}`,
    method: 'put',
    data: {
      user_id: userId,
      ...data
    }
  })
} 