export default {
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    back: 'Back',
    loading: 'Loading...',
    success: 'Success',
    error: 'Error',
    warning: 'Warning'
  },
  dashboard: {
    title: 'Dashboard',
    totalSessions: 'Total Sessions',
    totalMessages: 'Total Messages',
    totalTokens: 'Total Tokens',
    lastActive: 'Last Active',
    neverActive: 'Never Active'
  },
  auth: {
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    email: 'Email',
    password: 'Password',
    username: 'Username',
    forgotPassword: 'Forgot Password?',
    noAccount: 'No account?',
    hasAccount: 'Have an account?',
    resetPassword: 'Reset Password',
    verificationCode: 'Verification Code',
    sendCode: 'Send Code'
  },
  settings: {
    title: 'Settings',
    theme: {
      label: 'Theme',
      light: 'Light',
      dark: 'Dark'
    },
    language: {
      label: 'Language',
      zhCN: '中文',
      enUS: 'English'
    },
    model: {
      label: 'Default Model',
      glm: 'GLM-4-Plus',
      deepseek: 'Deepseek-R1 1.5B',
      qwen: 'Qwen2.5 1.5B',
      llama: 'LLaMA3.2 3B'
    },
    aiRules: {
      label: 'AI Personalization Rules',
      enable: 'Enable Rules',
      placeholder: 'Enter AI personalization rules...'
    }
  },
  chat: {
    newChat: 'New Chat',
    deleteChat: 'Delete Chat',
    clearHistory: 'Clear History',
    clearAllSessions: 'Clear All',
    darkMode: 'Dark Mode',
    lightMode: 'Light Mode',
    userCenter: 'User Center',
    logout: 'Logout',
    inputPlaceholder: 'Type a message...',
    enterShiftTip: 'Enter + Shift for new line',
    send: 'Send',
    thinking: 'AI is thinking...',
    uploadImage: 'Upload Image',
    imageLimit: 'Maximum 5 images allowed',
    confirm: {
      title: 'Confirm',
      cancel: 'Cancel',
      ok: 'OK',
      deleteSession: 'Are you sure you want to delete this session?',
      clearAll: 'Are you sure you want to clear all sessions?',
      logout: 'Are you sure you want to logout?'
    }
  },
  profile: {
    title: 'Profile',
    stats: {
      totalSessions: 'Total Sessions',
      totalMessages: 'Total Messages',
      totalTokens: 'Total Tokens',
      lastActive: 'Last Active'
    }
  },
  errors: {
    networkError: 'Network error, please try again later',
    serverError: 'Server error',
    unauthorized: 'Unauthorized, please login again',
    invalidInput: 'Invalid input',
    unknown: 'Unknown error'
  },
  sync: {
    title: 'Data Sync',
    lastSyncTime: 'Last Sync Time',
    unsyncedMessages: 'Unsynced Messages',
    unsyncedAdvice: 'Unsynced Advice',
    unsyncedDietRecords: 'Unsynced Diet Records',
    startSync: 'Start Sync',
    syncSuccess: 'Sync Successful',
    syncFailed: 'Sync Failed, Please Try Again Later',
    conflict: {
      title: 'Data Conflict',
      serverData: 'Server Data',
      clientData: 'Local Data',
      keepServer: 'Keep Server Data',
      keepClient: 'Keep Local Data',
      merge: 'Merge Data',
      resolveSuccess: 'Conflict Resolved Successfully',
      resolveFailed: 'Failed to Resolve Conflict'
    },
    types: {
      chat_records: 'Chat Records',
      health_advice: 'Health Advice',
      dietary_records: 'Diet Records',
      unknown: 'Unknown Type'
    }
  },
  userCenter: {
    title: 'User Center',
    menu: {
      profile: 'Profile',
      healthAdvice: 'Health Advice',
      dietaryRecord: 'Diet Records',
      dataAnalysis: 'Data Analysis'
    },
    quickAccess: {
      search: 'Search features or content...',
      shortcuts: {
        latestAdvice: 'Latest Advice',
        todayRecord: "Today's Record",
        healthReport: 'Health Report'
      }
    },
    actions: {
      backToChat: 'Back to Chat',
      refresh: 'Refresh',
      save: 'Save',
      edit: 'Edit'
    },
    loading: {
      default: 'Loading...',
      saving: 'Saving...',
      updating: 'Updating...'
    }
  },
  userProfile: {
    title: 'User Profile',
    labels: {
      username: 'Username',
      age: 'Age',
      gender: 'Gender',
      male: 'Male',
      female: 'Female',
      other: 'Other',
      height: 'Height (cm)',
      weight: 'Weight (kg)',
      healthGoal: 'Health Goal',
      dietType: 'Diet Type',
      spicyLevel: 'Spicy Level',
      favoriteIngredients: 'Favorite Ingredients',
      dislikedIngredients: 'Disliked Ingredients',
      cookingTime: 'Cooking Time Preference',
      dailyNutrition: 'Daily Nutrition Goals',
      targetWeight: 'Target Weight (kg)',
      allergies: 'Allergies',
      calories: 'Calories',
      protein: 'Protein',
      carbs: 'Carbohydrates',
      fat: 'Fat',
      minutes: 'minutes'
    },
    options: {
      healthGoal: {
        weight_loss: 'Weight Loss',
        weight_gain: 'Weight Gain',
        maintain_health: 'Maintain Health'
      },
      dietType: {
        normal: 'Regular',
        vegetarian: 'Vegetarian',
        vegan: 'Vegan',
        low_carb: 'Low Carb',
        keto: 'Keto',
        paleo: 'Paleo'
      },
      spicyLevel: {
        none: 'Not Spicy',
        mild: 'Mild',
        medium: 'Medium',
        hot: 'Hot',
        extra_hot: 'Extra Hot'
      },
      allergies: {
        peanuts: 'Peanuts',
        seafood: 'Seafood',
        dairy: 'Dairy',
        eggs: 'Eggs'
      }
    },
    actions: {
      edit: 'Edit',
      save: 'Save',
      cancel: 'Cancel'
    }
  },
  dataAnalysis: {
    title: 'Data Analysis',
    buttons: {
      refresh: 'Refresh',
      export: 'Export'
    },
    timeRange: {
      last7Days: 'Last 7 Days',
      last30Days: 'Last 30 Days',
      last90Days: 'Last 90 Days'
    },
    overview: {
      totalAdvices: 'Total Advices',
      averageRating: 'Average Rating'
    },
    userFeedback: 'User Feedback Analysis',
    ratingDistribution: 'Rating Distribution',
    feedbackTypeDistribution: 'Feedback Type Distribution',
    userAnalysis: 'User Situation Analysis',
    bmiIndex: 'BMI Index',
    adviceEffectComparison: 'Advice Type Effect Comparison'
  }
} 