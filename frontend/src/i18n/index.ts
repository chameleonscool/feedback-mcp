import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import zh from './locales/zh.json';
import en from './locales/en.json';

// 获取浏览器语言或默认使用中文
const getDefaultLanguage = (): string => {
  const savedLang = localStorage.getItem('language');
  if (savedLang) return savedLang;

  const browserLang = navigator.language.toLowerCase();
  if (browserLang.startsWith('zh')) return 'zh';
  return 'en';
};

i18n.use(initReactI18next).init({
  resources: {
    zh: { translation: zh },
    en: { translation: en },
  },
  lng: getDefaultLanguage(),
  fallbackLng: 'zh',
  interpolation: {
    escapeValue: false, // React 已经处理了 XSS
  },
});

export const changeLanguage = (lang: 'zh' | 'en') => {
  localStorage.setItem('language', lang);
  i18n.changeLanguage(lang);
};

export const getCurrentLanguage = (): 'zh' | 'en' => {
  return (i18n.language || 'zh') as 'zh' | 'en';
};

export default i18n;
