import request, { handleResponse } from './request';
import { storage } from '../utils/storage';
import axios from 'axios';
import { useLocalStorage } from '@vueuse/core';

// 设备ID存储
const deviceId = useLocalStorage('device_id', '');

export const authApi = {
  // 登录（支持用户名或邮箱）
  async login(identifier, password) {
    try {
      const response = await request.post('/auth/login', {
        identifier,
        password
      });
      const result = handleResponse(response);
      if (result.success) {
        storage.setToken(result.data.token);
        storage.setUser(result.data.user);
        deviceId.value = result.data.device_id;
      }
      return result;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败，请稍后重试'
      };
    }
  },

  // 注册
  async register(username, password, email, verifyCode) {
    try {
      const response = await request.post('/auth/register', {
        username,
        password,
        email,
        verification_code: verifyCode
      });
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '注册失败，请稍后重试'
      };
    }
  },

  // 发送验证码
  async sendVerifyCode(email) {
    try {
      const response = await request.post('/auth/send-verification', {
        email
      });
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '验证码发送失败，请稍后重试'
      };
    }
  },

  // 重置密码
  async resetPassword(email, newPassword, verifyCode) {
    try {
      const response = await request.post('/auth/reset-password', {
        email,
        new_password: newPassword,
        verification_code: verifyCode
      });
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '重置密码失败，请稍后重试'
      };
    }
  },

  // 获取用户信息
  async getUserInfo() {
    try {
      const response = await request.get('/auth/user-info');
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '获取用户信息失败'
      };
    }
  },

  // 更新用户信息
  async updateUserInfo(data) {
    try {
      const response = await request.put('/auth/user-info', data);
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '更新用户信息失败'
      };
    }
  },

  // 登出
  async logout() {
    try {
      const response = await request.post('/auth/logout');
      const result = handleResponse(response);
      if (result.success) {
        storage.clearAuth();
      }
      return result;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '登出失败，请稍后重试'
      };
    }
  },

  // 检查登录状态
  async checkLoginStatus() {
    try {
      const token = storage.getToken();
      if (!token) {
        return {
          success: false,
          message: '未登录'
        };
      }
      const response = await this.getUserInfo();
      return response;
    } catch (error) {
      return {
        success: false,
        message: '登录状态校验失败'
      };
    }
  },

  // 获取会话列表
  async listSessions() {
    return request.get('/sessions');
  },

  // 创建新会话
  async createSession(name = '新对话') {
    return request.post('/sessions/create', { session_name: name });
  },

  // 获取聊天历史
  async getChatHistory(sessionId) {
    return request.get(`/chat/history/${sessionId}`);
  },

  // 清空会话历史
  async clearHistory(sessionId) {
    return request.post(`/clear/${sessionId}`);
  },

  // 更新会话名称
  async updateSessionName(sessionId, newName) {
    try {
      const response = await request.put(`/sessions/${sessionId}/name`, {
        new_name: newName
      });
      return handleResponse(response);
    } catch (error) {
      console.error('更新会话名称失败:', error);
      throw error;
    }
  },

  // 获取会话最新消息
  async getLatestMessage(sessionId) {
    try {
      const response = await request.get(`/sessions/${sessionId}/latest-message`);
      return handleResponse(response);
    } catch (error) {
      console.error('获取最新消息失败:', error);
      throw error;
    }
  },

  // 删除会话
  async deleteSession(sessionId) {
    try {
      const response = await request.delete(`/sessions/${sessionId}`);
      return handleResponse(response);
    } catch (error) {
      console.error('删除会话失败:', error);
      throw error;
    }
  },

  // 清空所有会话
  async clearAllSessions() {
    try {
      const response = await request.delete('/sessions/clear/all');
      return handleResponse(response);
    } catch (error) {
      console.error('清空会话失败:', error);
      throw error;
    }
  },

  // 获取用户统计信息
  async getUserStats() {
    try {
      const response = await request.get('/user/stats');
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '获取用户统计信息失败'
      };
    }
  },

  // 获取用户偏好设置
  async getUserPreferences() {
    try {
      const response = await request({
        url: '/user/preferences',
        method: 'get'
      });
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '获取用户偏好设置失败'
      };
    }
  },

  // 更新用户偏好设置
  async updateUserPreferences(preferences) {
    try {
      const response = await request({
        url: '/user/preferences',
        method: 'put',
        data: {
          theme: preferences.theme,
          language: preferences.language,
          model: preferences.model,
          ai_rules: preferences.ai_rules,
          is_rules_enabled: preferences.is_rules_enabled
        }
      });
      return handleResponse(response);
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '更新用户偏好设置失败'
      };
    }
  }
};