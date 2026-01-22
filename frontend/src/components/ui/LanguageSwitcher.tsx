import { useTranslation } from 'react-i18next';
import { changeLanguage, getCurrentLanguage } from '@/i18n';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLang = getCurrentLanguage();

  const toggleLanguage = () => {
    const newLang = currentLang === 'zh' ? 'en' : 'zh';
    changeLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="
        px-3 py-1.5 rounded-lg
        bg-slate-700/50 hover:bg-slate-600/50
        text-sm text-slate-300
        transition-colors duration-200
        flex items-center gap-2
      "
      title={currentLang === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      <span className="text-base">🌐</span>
      <span>{currentLang === 'zh' ? 'EN' : '中'}</span>
    </button>
  );
}
