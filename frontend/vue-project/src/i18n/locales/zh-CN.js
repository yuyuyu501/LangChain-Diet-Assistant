export default {
  common: {
    confirm: '确定',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    back: '返回',
    loading: '加载中...',
    success: '操作成功',
    error: '操作失败',
    warning: '警告'
  },
  dashboard: {
    title: '仪表盘',
    totalSessions: '总会话数',
    totalMessages: '总消息数',
    totalTokens: '总Token数',
    lastActive: '最近活跃',
    neverActive: '从未活跃'
  },
  auth: {
    login: '登录',
    register: '注册',
    logout: '退出登录',
    email: '邮箱',
    password: '密码',
    username: '用户名',
    forgotPassword: '忘记密码？',
    noAccount: '还没有账户？',
    hasAccount: '已有账户？',
    resetPassword: '重置密码',
    verificationCode: '验证码',
    sendCode: '发送验证码'
  },
  settings: {
    title: '设置',
    theme: {
      label: '主题',
      light: '浅色',
      dark: '深色'
    },
    language: {
      label: '语言',
      zhCN: '中文',
      enUS: 'English'
    },
    model: {
      label: '默认模型',
      glm: 'GLM-4-Plus',
      deepseek: 'Deepseek-R1 1.5B',
      qwen: 'Qwen2.5 1.5B',
      llama: 'LLaMA3.2 3B'
    },
    aiRules: {
      label: 'AI个性化规则',
      enable: '启用规则',
      placeholder: '请输入AI个性化规则...'
    }
  },
  chat: {
    newChat: '新建会话',
    deleteChat: '删除会话',
    clearHistory: '清空历史',
    clearAllSessions: '清空会话',
    darkMode: '夜间模式',
    lightMode: '日间模式',
    userCenter: '个人中心',
    logout: '退出登录',
    inputPlaceholder: '输入消息...',
    enterShiftTip: 'Enter + Shift换行',
    send: '发送',
    thinking: 'AI正在思考中...',
    uploadImage: '上传图片',
    imageLimit: '最多上传5张图片',
    confirm: {
      title: '确认',
      cancel: '取消',
      ok: '确定',
      deleteSession: '确定要删除这个会话吗？',
      clearAll: '确定要清空所有会话吗？',
      logout: '确定要退出登录吗？'
    }
  },
  profile: {
    title: '个人中心',
    stats: {
      totalSessions: '总会话数',
      totalMessages: '总消息数',
      totalTokens: '总Token数',
      lastActive: '最后活跃'
    }
  },
  errors: {
    networkError: '网络错误，请稍后重试',
    serverError: '服务器错误',
    unauthorized: '未授权，请重新登录',
    invalidInput: '输入无效',
    unknown: '未知错误'
  },
  sync: {
    title: '数据同步',
    lastSyncTime: '最后同步时间',
    unsyncedMessages: '未同步消息',
    unsyncedAdvice: '未同步建议',
    unsyncedDietRecords: '未同步饮食记录',
    startSync: '开始同步',
    syncSuccess: '同步成功',
    syncFailed: '同步失败，请稍后重试',
    conflict: {
      title: '数据冲突',
      serverData: '服务器数据',
      clientData: '本地数据',
      keepServer: '保留服务器数据',
      keepClient: '保留本地数据',
      merge: '合并数据',
      resolveSuccess: '冲突解决成功',
      resolveFailed: '解决冲突失败'
    },
    types: {
      chat_records: '聊天记录',
      health_advice: '健康建议',
      dietary_records: '饮食记录',
      unknown: '未知类型'
    }
  },
  userCenter: {
    title: '个人中心',
    menu: {
      profile: '基本信息',
      healthAdvice: '健康建议',
      dietaryRecord: '饮食记录',
      dataAnalysis: '数据分析'
    },
    quickAccess: {
      search: '搜索功能或内容...',
      shortcuts: {
        latestAdvice: '最新建议',
        todayRecord: '今日记录',
        healthReport: '健康报告'
      }
    },
    actions: {
      backToChat: '返回聊天',
      refresh: '刷新',
      save: '保存',
      edit: '编辑'
    },
    loading: {
      default: '加载中...',
      saving: '保存中...',
      updating: '更新中...'
    }
  },
  userProfile: {
    title: '个人档案',
    labels: {
      username: '用户名',
      age: '年龄',
      gender: '性别',
      male: '男',
      female: '女',
      other: '其他',
      height: '身高(cm)',
      weight: '体重(kg)',
      healthGoal: '健康目标',
      dietType: '饮食类型',
      spicyLevel: '辣度偏好',
      favoriteIngredients: '喜爱的食材',
      dislikedIngredients: '不喜欢的食材',
      cookingTime: '烹饪时间偏好',
      dailyNutrition: '每日营养目标',
      targetWeight: '目标体重(kg)',
      allergies: '过敏原',
      calories: '卡路里',
      protein: '蛋白质',
      carbs: '碳水化合物',
      fat: '脂肪',
      minutes: '分钟'
    },
    options: {
      healthGoal: {
        weight_loss: '减重',
        weight_gain: '增重',
        maintain_health: '保持健康'
      },
      dietType: {
        normal: '普通',
        vegetarian: '素食',
        vegan: '纯素',
        low_carb: '低碳水',
        keto: '生酮',
        paleo: '古法'
      },
      spicyLevel: {
        none: '不辣',
        mild: '微辣',
        medium: '中辣',
        hot: '重辣',
        extra_hot: '特辣'
      },
      allergies: {
        peanuts: '花生',
        seafood: '海鲜',
        dairy: '乳制品',
        eggs: '鸡蛋'
      }
    },
    actions: {
      edit: '编辑',
      save: '保存',
      cancel: '取消'
    }
  },
  dataAnalysis: {
    title: '数据分析',
    buttons: {
      refresh: '刷新',
      export: '导出'
    },
    timeRange: {
      last7Days: '近7天',
      last30Days: '近30天',
      last90Days: '近90天'
    },
    overview: {
      totalAdvices: '建议总数',
      averageRating: '平均评分'
    },
    userFeedback: '用户反馈分析',
    ratingDistribution: '评分分布',
    feedbackTypeDistribution: '反馈类型分布',
    userAnalysis: '用户情况分析',
    bmiIndex: 'BMI指数',
    adviceEffectComparison: '建议类型效果对比'
  }
} 