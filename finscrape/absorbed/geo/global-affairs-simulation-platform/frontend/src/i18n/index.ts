import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import zh from './locales/zh.json'
import en from './locales/en.json'

const savedLang = localStorage.getItem('ir_platform_lang')
const browserLang = navigator.language?.toLowerCase().startsWith('zh') ? 'zh' : 'en'

i18n
  .use(initReactI18next)
  .init({
    resources: {
      zh: { translation: zh },
      en: { translation: en },
    },
    lng: savedLang || browserLang,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  })

i18n.on('languageChanged', (lng) => {
  localStorage.setItem('ir_platform_lang', lng)
  document.documentElement.lang = lng
})

document.documentElement.lang = i18n.language

export default i18n
