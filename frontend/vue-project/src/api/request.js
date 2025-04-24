import axios from 'axios';
import router from '../router';
import { storage } from '../utils/storage';
import { ElMessage } from 'element-plus';

// 创建axios实例
const request = axios.create({
  baseURL: 'http://localhost:8000',  // backend服务
  timeout: 120000,  // 增加到120秒
  headers: {
    'Content-Type': 'application/json',
  },
});

// 创建robot服务的axios实例
export const robotRequest = axios.create({
  baseURL: 'http://localhost:8001',  // robot服务端口
  timeout: 120000,  // 增加到120秒
  headers: {
    'Content-Type': 'application/json',
  },
});

// 统一响应处理
export const handleResponse = (response) => {
  const { success, message, data } = response;
  if (!success) {
    throw new Error(message);
  }
  return { success, message, data };
};

// 请求拦截器
const addAuthHeader = (config) => {
  const token = storage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

request.interceptors.request.use(addAuthHeader, (error) => Promise.reject(error));
robotRequest.interceptors.request.use(addAuthHeader, (error) => Promise.reject(error));

// 响应拦截器
const handleResponseError = (error) => {
  if (error.response) {
    switch (error.response.status) {
      case 401:
        // 只在非首次加载且非登录页面时清除认证信息并跳转
        if (window.location.pathname !== '/auth' && document.readyState === 'complete') {
          storage.clearAuth();
          router.push('/auth');
        }
        break;
      case 403:
        // 权限不足
        console.error('权限不足');
        break;
      case 404:
        // 资源不存在
        console.error('请求的资源不存在');
        break;
      case 500:
        // 服务器错误
        console.error('服务器错误');
        break;
    }
  }
  return Promise.reject(error);
};

const handleResponseSuccess = (response) => response.data;

request.interceptors.response.use(handleResponseSuccess, handleResponseError);
robotRequest.interceptors.response.use(handleResponseSuccess, handleResponseError);

export default request; 