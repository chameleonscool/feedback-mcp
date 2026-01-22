import axios from 'axios';
import { getApiKey, getAdminSession } from '@/utils/storage';

/**
 * Axios 实例 - 用于用户 API 请求
 * 自动添加 Authorization Header
 */
export const api = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Authorization Header
api.interceptors.request.use(
  (config) => {
    const apiKey = getApiKey();
    if (apiKey) {
      config.headers.Authorization = `Bearer ${apiKey}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 认证失败，可能需要重新登录
      console.warn('Authentication failed');
    }
    return Promise.reject(error);
  }
);

/**
 * Axios 实例 - 用于管理员 API 请求
 * 使用 session token 认证
 */
export const adminApi = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Admin 请求拦截器
adminApi.interceptors.request.use(
  (config) => {
    const token = getAdminSession();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
