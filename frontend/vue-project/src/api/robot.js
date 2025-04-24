import { robotRequest as request } from './request'
import { getDeviceId } from './sync'  // 导入 getDeviceId 函数

export const robotApi = {
  // 发送消息到robot服务
  sendMessage: (sessionId, message, images = []) => {
    return request({
      url: '/api/chat',
      method: 'post',
      data: {
        session_id: sessionId,
        message: message,
        images: images,
        device_id: getDeviceId()  // 添加 device_id
      }
    })
  },
  // 切换模型
  async switchModel(model) {
    try {
      const response = await request.post('/api/switch_model', { model });
      return {
        success: response.success,
        message: response.message || '模型切换成功'
      };
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.error || '模型切换失败'
      };
    }
  },
  // 获取用户规则
  async getUserRules() {
    try {
      const response = await request.get('/api/user_rules'); 
      if (response.success) {
        return {
          success: true,
          data: response.data
        };
      } else {
        throw new Error(response.message || '获取用户规则失败');
      }
    } catch (error) {
      console.error('获取用户规则失败:', error);
      return {
        success: false,
        message: error.response?.data?.error || error.message || '获取用户规则失败'
      };
    }
  }
} 