import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '@/store';

/**
 * 类型化的 useDispatch hook
 */
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();

/**
 * 类型化的 useSelector hook
 */
export const useAppSelector = useSelector.withTypes<RootState>();
