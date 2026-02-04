import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * 通知铃声 Hook
 * 用于播放新消息提示音
 */
export function useNotificationSound() {
  const [soundEnabled, setSoundEnabled] = useState<boolean>(() => {
    const saved = localStorage.getItem('soundEnabled');
    return saved !== null ? saved === 'true' : true; // 默认开启
  });

  const audioContextRef = useRef<AudioContext | null>(null);

  const toggleSound = useCallback(() => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    localStorage.setItem('soundEnabled', String(newValue));
  }, [soundEnabled]);

  // 播放提示铃声
  const playNotificationSound = useCallback(() => {
    if (!soundEnabled) return;

    try {
      // 创建或复用 AudioContext
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext })
            .webkitAudioContext)();
      }
      const ctx = audioContextRef.current;

      // 创建振荡器生成铃声
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      // 设置铃声音调（两个音符的简单铃声）
      oscillator.frequency.setValueAtTime(880, ctx.currentTime); // A5
      oscillator.frequency.setValueAtTime(1046.5, ctx.currentTime + 0.1); // C6

      // 设置音量衰减
      gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + 0.3);
    } catch (e) {
      console.warn('Failed to play notification sound:', e);
    }
  }, [soundEnabled]);

  return {
    soundEnabled,
    toggleSound,
    playNotificationSound,
  };
}

/**
 * 检测新任务并播放铃声的 Hook
 */
export function useNewTaskNotification(
  taskIds: string[],
  playSound: () => void
) {
  const prevIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const currentIds = new Set(taskIds);
    const prevIds = prevIdsRef.current;

    // 检查是否有新任务（当前有的 ID 但之前没有的）
    let hasNewTask = false;
    for (const id of currentIds) {
      if (!prevIds.has(id)) {
        hasNewTask = true;
        break;
      }
    }

    // 只在非首次加载时播放铃声（首次加载 prevIds 为空）
    if (hasNewTask && prevIds.size > 0) {
      playSound();
    }

    // 更新引用
    prevIdsRef.current = currentIds;
  }, [taskIds, playSound]);
}
