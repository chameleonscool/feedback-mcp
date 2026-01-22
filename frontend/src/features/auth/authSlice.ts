import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { AuthState } from '@/types';
import {
  saveApiKey,
  getApiKey,
  getApiKeyExpiry,
  clearApiKey,
} from '@/utils/storage';

const initialState: AuthState = {
  apiKey: null,
  apiKeyExpiry: null,
  isAuthenticated: false,
  loginStatus: 'idle',
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /**
     * 设置 API Key
     * 同时保存到 localStorage
     */
    setApiKey: (state, action: PayloadAction<string>) => {
      const apiKey = action.payload;
      saveApiKey(apiKey);
      
      state.apiKey = apiKey;
      state.apiKeyExpiry = getApiKeyExpiry();
      state.isAuthenticated = true;
      state.loginStatus = 'succeeded';
    },

    /**
     * 清除 API Key
     * 同时清除 localStorage
     */
    clearAuth: (state) => {
      clearApiKey();
      
      state.apiKey = null;
      state.apiKeyExpiry = null;
      state.isAuthenticated = false;
      state.loginStatus = 'idle';
    },

    /**
     * 从 localStorage 加载缓存的认证信息
     */
    loadCachedAuth: (state) => {
      const apiKey = getApiKey();
      const expiry = getApiKeyExpiry();

      if (apiKey && expiry && Date.now() < expiry) {
        state.apiKey = apiKey;
        state.apiKeyExpiry = expiry;
        state.isAuthenticated = true;
        state.loginStatus = 'succeeded';
      } else {
        // 清除过期的缓存
        clearApiKey();
        state.apiKey = null;
        state.apiKeyExpiry = null;
        state.isAuthenticated = false;
        state.loginStatus = 'idle';
      }
    },

    /**
     * 设置登录状态
     */
    setLoginStatus: (state, action: PayloadAction<AuthState['loginStatus']>) => {
      state.loginStatus = action.payload;
    },
  },
});

export const { setApiKey, clearAuth, loadCachedAuth, setLoginStatus } =
  authSlice.actions;

export default authSlice.reducer;
