export const validators = {
  // 必填验证
  required: (value) => {
    if (value === null || value === undefined || value === '') {
      return '此字段不能为空';
    }
    return true;
  },

  // 邮箱验证
  email: (value) => {
    if (!value) return true;
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(value) ? true : '请输入有效的邮箱地址';
  },

  // 用户名验证
  username: (value) => {
    if (!value) return true;
    const pattern = /^[a-zA-Z0-9_]{4,20}$/;
    return pattern.test(value) ? true : '用户名必须是4-20位字母、数字或下划线';
  },

  // 密码验证
  password: (value) => {
    if (!value) return true;
    const pattern = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
    return pattern.test(value) ? true : '密码必须至少包含8个字符，包括字母和数字';
  },

  // 确认密码验证
  confirmPassword: (password) => (value) => {
    if (!value) return true;
    return value === password ? true : '两次输入的密码不一致';
  },

  // 验证码验证
  verifyCode: (value) => {
    if (!value) return true;
    const pattern = /^\d{6}$/;
    return pattern.test(value) ? true : '请输入6位数字验证码';
  }
}; 