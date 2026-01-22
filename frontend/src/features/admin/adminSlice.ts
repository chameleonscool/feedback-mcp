import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import type { AdminState, AdminUser, SystemStats } from '@/types';
import { adminApi } from '@/services/api';
import {
  saveAdminSession,
  getAdminSession,
  clearAdminSession,
} from '@/utils/storage';

const initialState: AdminState = {
  sessionToken: null,
  isAuthenticated: false,
  users: [],
  stats: null,
};

/**
 * 管理员登录
 */
export const adminLogin = createAsyncThunk(
  'admin/login',
  async (credentials: { username: string; password: string }) => {
    const response = await adminApi.post<{ session_token: string }>(
      '/api/admin/login',
      credentials
    );
    return response.data.session_token;
  }
);

/**
 * 管理员登出
 */
export const adminLogout = createAsyncThunk('admin/logout', async () => {
  try {
    await adminApi.post('/api/admin/logout');
  } catch {
    // Ignore errors
  }
  clearAdminSession();
});

/**
 * 验证管理员会话
 */
export const verifyAdminSession = createAsyncThunk(
  'admin/verifySession',
  async () => {
    const response = await adminApi.get<{ users: AdminUser[] }>(
      '/api/admin/users'
    );
    return response.data;
  }
);

/**
 * 获取用户列表
 */
export const fetchAdminUsers = createAsyncThunk(
  'admin/fetchUsers',
  async () => {
    const response = await adminApi.get<{ users: AdminUser[] }>(
      '/api/admin/users'
    );
    return response.data.users;
  }
);

/**
 * 更新飞书配置
 */
export const updateFeishuConfig = createAsyncThunk(
  'admin/updateFeishuConfig',
  async (config: {
    app_id: string;
    app_secret?: string;
    redirect_uri: string;
  }) => {
    await adminApi.post('/api/admin/feishu/config', config);
    return true;
  }
);

/**
 * 修改管理员密码
 */
export const changeAdminPassword = createAsyncThunk(
  'admin/changePassword',
  async (passwords: { old_password: string; new_password: string }) => {
    await adminApi.post('/api/admin/change-password', passwords);
    return true;
  }
);

export const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    /**
     * 设置会话令牌
     */
    setSessionToken: (state, action: PayloadAction<string>) => {
      const token = action.payload;
      saveAdminSession(token);
      state.sessionToken = token;
      state.isAuthenticated = true;
    },

    /**
     * 从 localStorage 加载缓存的会话
     */
    loadCachedSession: (state) => {
      const token = getAdminSession();
      if (token) {
        state.sessionToken = token;
        state.isAuthenticated = true;
      }
    },

    /**
     * 清除会话
     */
    clearSession: (state) => {
      clearAdminSession();
      state.sessionToken = null;
      state.isAuthenticated = false;
      state.users = [];
      state.stats = null;
    },

    /**
     * 设置统计信息
     */
    setStats: (state, action: PayloadAction<SystemStats>) => {
      state.stats = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // adminLogin
      .addCase(adminLogin.fulfilled, (state, action) => {
        const token = action.payload;
        saveAdminSession(token);
        state.sessionToken = token;
        state.isAuthenticated = true;
      })
      .addCase(adminLogin.rejected, (state) => {
        state.isAuthenticated = false;
        state.sessionToken = null;
      })

      // adminLogout
      .addCase(adminLogout.fulfilled, (state) => {
        state.sessionToken = null;
        state.isAuthenticated = false;
        state.users = [];
        state.stats = null;
      })

      // verifyAdminSession
      .addCase(verifyAdminSession.fulfilled, (state) => {
        state.isAuthenticated = true;
      })
      .addCase(verifyAdminSession.rejected, (state) => {
        clearAdminSession();
        state.sessionToken = null;
        state.isAuthenticated = false;
      })

      // fetchAdminUsers
      .addCase(fetchAdminUsers.fulfilled, (state, action) => {
        state.users = action.payload;
        state.stats = {
          userCount: action.payload.length,
          todayRequests: 0,
          version: 'v0.9.0',
        };
      });
  },
});

export const {
  setSessionToken,
  loadCachedSession,
  clearSession,
  setStats,
} = adminSlice.actions;

export default adminSlice.reducer;
