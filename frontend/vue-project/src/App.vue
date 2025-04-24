<template>
  <div class="app-container">
    <el-config-provider :locale="currentLocale">
      <router-view />
    </el-config-provider>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { storage } from '@/utils/storage'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import enUs from 'element-plus/dist/locale/en.mjs'
import { authApi } from '@/api/auth'

const { locale } = useI18n()
const currentLocale = ref(zhCn)

// 监听语言变化
watch(() => locale.value, (newLocale) => {
  currentLocale.value = newLocale === 'zh-CN' ? zhCn : enUs
  storage.setLanguage(newLocale)
})

// 从后端获取用户偏好设置
const fetchUserPreferences = async () => {
  try {
    const token = storage.getToken()
    if (token) {
      const response = await authApi.getUserPreferences()
      if (response.success) {
        const { language, theme } = response.data
        // 设置语言
        if (language) {
          locale.value = language
          currentLocale.value = language === 'zh-CN' ? zhCn : enUs
          storage.setLanguage(language)
        }
        // 设置主题
        if (theme === 'dark') {
          document.body.classList.add('dark-mode')
          storage.setDarkMode(true)
        } else {
          document.body.classList.remove('dark-mode')
          storage.setDarkMode(false)
        }
      }
    }
  } catch (error) {
    console.error('获取用户偏好设置失败:', error)
    // 如果获取失败，使用本地存储的设置作为后备
    const savedLanguage = storage.getLanguage()
    locale.value = savedLanguage
    currentLocale.value = savedLanguage === 'zh-CN' ? zhCn : enUs
    
    const isDarkMode = storage.getDarkMode()
    if (isDarkMode) {
      document.body.classList.add('dark-mode')
    }
  }
}

onMounted(() => {
  fetchUserPreferences()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  line-height: 1.6;
  color: #333;
}

#app {
  height: 100vh;
}

.app-container {
  height: 100vh;
  width: 100vw;
}

body.dark-mode {
  background-color: #1a1a1a;
  color: #fff;
}
</style>