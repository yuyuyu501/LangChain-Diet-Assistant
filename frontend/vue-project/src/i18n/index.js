import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'
import { storage } from '../utils/storage'

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS
}

const i18n = createI18n({
  legacy: false, // 使用组合式API
  locale: storage.getLanguage() || 'zh-CN', // 从本地存储获取语言设置，默认中文
  fallbackLocale: 'zh-CN', // 回退语言
  messages
})

export default i18n 