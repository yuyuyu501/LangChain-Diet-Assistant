const TOKEN_KEY = 'token';
const USER_KEY = 'user';
const DARK_MODE_KEY = 'darkMode';

export const storage = {
  // Token 相关操作
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  },
  removeToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  // 用户信息相关操作
  getUser() {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  },
  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify({
      user_id: user.user_id,
      username: user.username,
      email: user.email,
      device_id: user.device_id
    }));
  },
  removeUser() {
    localStorage.removeItem(USER_KEY);
  },

  // 暗黑模式相关操作
  getDarkMode() {
    return localStorage.getItem(DARK_MODE_KEY) === 'true';
  },
  setDarkMode(isDark) {
    localStorage.setItem(DARK_MODE_KEY, isDark);
  },

  // 语言相关操作
  getLanguage() {
    return localStorage.getItem('language') || 'zh-CN';
  },
  setLanguage(lang) {
    localStorage.setItem('language', lang);
  },

  // 清除所有认证相关信息
  clearAuth() {
    this.removeToken();
    this.removeUser();
  }
}; 