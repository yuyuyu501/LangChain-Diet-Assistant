<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2 class="title">AI营养助手</h2>
      <p class="subtitle">
        {{ currentView === 'login' ? '登录到您的账户' : 
           currentView === 'register' ? '创建新账户' : 
           '重置您的密码' }}
      </p>
      
      <!-- 登录表单 -->
      <form v-if="currentView === 'login'" @submit.prevent="handleLogin">
        <div class="form-group">
          <label>邮箱/用户名</label>
          <input type="text" v-model="loginForm.identifier" placeholder="请输入邮箱或用户名" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <div class="password-input">
            <input :type="showPassword ? 'text' : 'password'" v-model="loginForm.password" placeholder="请输入密码" required>
            <i class="password-toggle" @click="showPassword = !showPassword" :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </div>
        </div>
        <div class="forgot-password">
          <a href="#" @click.prevent="currentView = 'resetPassword'" class="forgot-link">忘记密码？</a>
        </div>
        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <div class="signup-link">
          还没有账户？ <a href="#" @click.prevent="currentView = 'register'">立即注册</a>
        </div>
      </form>
      
      <!-- 注册表单 -->
      <form v-else-if="currentView === 'register'" @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名</label>
          <input type="text" v-model="registerForm.username" required>
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input type="email" v-model="registerForm.email" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <div class="password-input">
            <input :type="showRegisterPassword ? 'text' : 'password'" v-model="registerForm.password" required>
            <i class="password-toggle" @click="showRegisterPassword = !showRegisterPassword" :class="showRegisterPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </div>
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <div class="password-input">
            <input :type="showConfirmPassword ? 'text' : 'password'" v-model="registerForm.confirmPassword" required>
            <i class="password-toggle" @click="showConfirmPassword = !showConfirmPassword" :class="showConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </div>
        </div>
        <div class="form-group">
          <label>验证码</label>
          <div class="verify-code">
            <input type="text" v-model="registerForm.verifyCode" required>
            <button type="button" @click="sendVerifyCode(registerForm.email)" :disabled="cooldown > 0">
              {{ cooldown > 0 ? `${cooldown}s` : '发送验证码' }}
            </button>
          </div>
        </div>
        <button type="submit" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
        <div class="form-links">
          <a href="#" @click.prevent="currentView = 'login'">已有账号？立即登录</a>
        </div>
      </form>

      <!-- 重置密码表单 -->
      <form v-else @submit.prevent="handleResetPassword">
        <div class="form-group">
          <label>邮箱</label>
          <input type="email" v-model="resetForm.email" required>
        </div>
        <div class="form-group">
          <label>验证码</label>
          <div class="verify-code">
            <input type="text" v-model="resetForm.verifyCode" required>
            <button type="button" @click="sendVerifyCode(resetForm.email)" :disabled="cooldown > 0 || sendingCode">
              {{ cooldown > 0 ? `${cooldown}s` : sendingCode ? '发送中...' : '发送验证码' }}
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>新密码</label>
          <div class="password-input">
            <input :type="showResetPassword ? 'text' : 'password'" v-model="resetForm.newPassword" required>
            <i class="password-toggle" @click="showResetPassword = !showResetPassword" :class="showResetPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </div>
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <div class="password-input">
            <input :type="showResetConfirmPassword ? 'text' : 'password'" v-model="resetForm.confirmPassword" required>
            <i class="password-toggle" @click="showResetConfirmPassword = !showResetConfirmPassword" :class="showResetConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </div>
        </div>
        <button type="submit" :disabled="loading">{{ loading ? '重置中...' : '重置密码' }}</button>
        <div class="form-links">
          <a href="#" @click.prevent="currentView = 'login'">返回登录</a>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import { storage } from '@/utils/storage'

const router = useRouter()
const currentView = ref('login')
const loading = ref(false)
const cooldown = ref(0)
const sendingCode = ref(false)
const showPassword = ref(false)
const showRegisterPassword = ref(false)
const showConfirmPassword = ref(false)
const showResetPassword = ref(false)
const showResetConfirmPassword = ref(false)

// 登录表单数据
const loginForm = reactive({
  identifier: '',
  password: ''
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  verifyCode: ''
})

// 重置密码表单数据
const resetForm = reactive({
  email: '',
  verifyCode: '',
  newPassword: '',
  confirmPassword: ''
})

// 清除任何可能存在的认证信息
onMounted(() => {
  storage.clearAuth()
})

// 处理登录
const handleLogin = async () => {
  try {
    loading.value = true
    const res = await authApi.login(loginForm.identifier, loginForm.password)
    if (res.success) {
      storage.setToken(res.data.token)
      storage.setUser(res.data.user)
      await router.push('/chat')
    } else {
      alert(res.message || '登录失败')
    }
  } catch (error) {
    console.error('登录失败:', error)
    alert(error.message || '登录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 处理注册
const handleRegister = async () => {
  if (registerForm.password !== registerForm.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }
  
  try {
    loading.value = true
    const res = await authApi.register(
      registerForm.username,
      registerForm.password,
      registerForm.email,
      registerForm.verifyCode
    )
    if (res.success) {
      alert('注册成功，请登录')
      currentView.value = 'login'
    }
  } catch (error) {
    console.error('注册失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理重置密码
const handleResetPassword = async () => {
  if (resetForm.newPassword !== resetForm.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }

  try {
    loading.value = true
    const res = await authApi.resetPassword(
      resetForm.email,
      resetForm.newPassword,
      resetForm.verifyCode
    )
    if (res.success) {
      alert('密码重置成功，请登录')
      currentView.value = 'login'
    }
  } catch (error) {
    console.error('重置密码失败:', error)
  } finally {
    loading.value = false
  }
}

// 发送验证码
const sendVerifyCode = async (email) => {
  if (cooldown.value > 0) return
  if (!email) {
    alert('请输入邮箱地址')
    return
  }
  
  try {
    sendingCode.value = true
    const res = await authApi.sendVerifyCode(email)
    if (res.success) {
      alert('验证码已发送，请查收邮件')
      cooldown.value = 60
      const timer = setInterval(() => {
        cooldown.value--
        if (cooldown.value <= 0) {
          clearInterval(timer)
        }
      }, 1000)
    } else {
      alert(res.message || '发送验证码失败')
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
    alert(error.message || '发送验证码失败，请稍后重试')
  } finally {
    sendingCode.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #1a2035, #1f2940);
}

.auth-card {
  background: rgba(31, 41, 64, 0.95);
  padding: 2.5rem;
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(10px);
  animation: fadeIn 0.3s ease, slideUp 0.3s ease;
}

.title {
  color: #ffffff;
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #8f9bba;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #8f9bba;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
  font-size: 1rem;
  transition: all 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #6c63ff;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2);
}

.password-input {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #000000;
  font-size: 1.2rem;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  opacity: 0.8;
}

.password-toggle:hover {
  color: #6c63ff;
  opacity: 1;
}

.verify-code {
  display: flex;
  gap: 1rem;
}

.verify-code input {
  flex: 1;
}

.verify-code button {
  padding: 0 1.5rem;
  background: rgba(108, 99, 255, 0.1);
  color: #6c63ff;
  border: 1px solid #6c63ff;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.verify-code button:hover:not(:disabled) {
  background: rgba(108, 99, 255, 0.2);
}

.verify-code button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button[type="submit"] {
  width: 100%;
  padding: 0.8rem;
  background: #6c63ff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 1rem;
}

button[type="submit"]:hover:not(:disabled) {
  background: #5b52e5;
  transform: translateY(-1px);
}

button[type="submit"]:disabled {
  background: #4a4a4a;
  cursor: not-allowed;
}

.form-links, .signup-link {
  text-align: center;
  margin-top: 1.5rem;
  color: #8f9bba;
  font-size: 0.9rem;
}

.form-links a, .signup-link a, .forgot-link {
  color: #6c63ff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.form-links a:hover, .signup-link a:hover, .forgot-link:hover {
  color: #5b52e5;
  text-decoration: underline;
}

.forgot-password {
  text-align: right;
  margin: -0.5rem 0 1rem;
}

/* 添加动画效果 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* 输入框占位符样式 */
input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
</style> 