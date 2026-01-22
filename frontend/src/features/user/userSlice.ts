import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import type { UserProfile, UserState } from '@/types';
import { api } from '@/services/api';

const initialState: UserState = {
  profile: null,
  feishuNotifyEnabled: false,
  loadingStatus: 'idle',
};

/**
 * 获取用户信息
 */
export const fetchUserInfo = createAsyncThunk(
  'user/fetchInfo',
  async () => {
    const response = await api.get<{
      open_id: string;
      name: string;
      avatar_url?: string;
      email?: string;
      is_active: boolean;
    }>('/api/user/info');
    
    // 转换为驼峰命名
    return {
      openId: response.data.open_id,
      name: response.data.name,
      avatarUrl: response.data.avatar_url,
      email: response.data.email,
      isActive: response.data.is_active,
    } as UserProfile;
  }
);

/**
 * 获取飞书通知状态
 */
export const fetchFeishuNotifyStatus = createAsyncThunk(
  'user/fetchFeishuNotify',
  async () => {
    const response = await api.get<{ enabled: boolean }>('/api/user/feishu-notify');
    return response.data.enabled;
  }
);

/**
 * 更新飞书通知状态
 */
export const updateFeishuNotify = createAsyncThunk(
  'user/updateFeishuNotify',
  async (enabled: boolean) => {
    await api.post('/api/user/feishu-notify', { enabled });
    return enabled;
  }
);

export const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    /**
     * 设置用户信息
     */
    setProfile: (state, action: PayloadAction<UserProfile | null>) => {
      state.profile = action.payload;
    },

    /**
     * 清除用户信息
     */
    clearProfile: (state) => {
      state.profile = null;
      state.feishuNotifyEnabled = false;
      state.loadingStatus = 'idle';
    },

    /**
     * 设置飞书通知状态
     */
    setFeishuNotify: (state, action: PayloadAction<boolean>) => {
      state.feishuNotifyEnabled = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchUserInfo
      .addCase(fetchUserInfo.pending, (state) => {
        state.loadingStatus = 'loading';
      })
      .addCase(fetchUserInfo.fulfilled, (state, action) => {
        state.profile = action.payload;
        state.loadingStatus = 'succeeded';
      })
      .addCase(fetchUserInfo.rejected, (state) => {
        state.loadingStatus = 'failed';
      })
      
      // fetchFeishuNotifyStatus
      .addCase(fetchFeishuNotifyStatus.fulfilled, (state, action) => {
        state.feishuNotifyEnabled = action.payload;
      })
      
      // updateFeishuNotify
      .addCase(updateFeishuNotify.fulfilled, (state, action) => {
        state.feishuNotifyEnabled = action.payload;
      });
  },
});

export const { setProfile, clearProfile, setFeishuNotify } = userSlice.actions;

export default userSlice.reducer;
