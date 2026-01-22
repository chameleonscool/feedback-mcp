/**
 * API Key 存储工具
 * 使用 localStorage 存储 API Key，30 天有效期
 */

const API_KEY_STORAGE_KEY = 'userApiKey';
const API_KEY_EXPIRY_KEY = 'userApiKeyExpiry';
const CACHE_DAYS = 30;

/**
 * 保存 API Key 到 localStorage
 * @param apiKey API Key
 */
export function saveApiKey(apiKey: string): void {
  const expiryDate = new Date();
  expiryDate.setDate(expiryDate.getDate() + CACHE_DAYS);
  
  localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
  localStorage.setItem(API_KEY_EXPIRY_KEY, expiryDate.getTime().toString());
}

/**
 * 获取缓存的 API Key
 * 如果已过期，返回 null 并清除缓存
 * @returns API Key 或 null
 */
export function getApiKey(): string | null {
  const apiKey = localStorage.getItem(API_KEY_STORAGE_KEY);
  const expiry = localStorage.getItem(API_KEY_EXPIRY_KEY);
  
  if (!apiKey || !expiry) {
    return null;
  }
  
  // 检查是否过期
  if (Date.now() > parseInt(expiry, 10)) {
    clearApiKey();
    return null;
  }
  
  return apiKey;
}

/**
 * 获取 API Key 过期时间
 * @returns 过期时间戳或 null
 */
export function getApiKeyExpiry(): number | null {
  const expiry = localStorage.getItem(API_KEY_EXPIRY_KEY);
  return expiry ? parseInt(expiry, 10) : null;
}

/**
 * 清除缓存的 API Key
 */
export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY);
  localStorage.removeItem(API_KEY_EXPIRY_KEY);
}

/**
 * 获取 API Key 剩余有效天数
 * @returns 剩余天数（0 表示已过期）
 */
export function getRemainingDays(): number {
  const expiry = localStorage.getItem(API_KEY_EXPIRY_KEY);
  if (!expiry) return 0;
  
  const remaining = parseInt(expiry, 10) - Date.now();
  if (remaining <= 0) return 0;
  
  return Math.ceil(remaining / (1000 * 60 * 60 * 24));
}

// Admin session storage
const ADMIN_SESSION_KEY = 'adminSession';

export function saveAdminSession(token: string): void {
  localStorage.setItem(ADMIN_SESSION_KEY, token);
}

export function getAdminSession(): string | null {
  return localStorage.getItem(ADMIN_SESSION_KEY);
}

export function clearAdminSession(): void {
  localStorage.removeItem(ADMIN_SESSION_KEY);
}
