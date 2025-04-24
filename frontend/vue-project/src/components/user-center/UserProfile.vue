<template>
  <div class="user-profile">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('userProfile.title') }}</span>
          <el-button type="primary" @click="handleEdit">{{ t('userProfile.actions.edit') }}</el-button>
        </div>
      </template>
      
      <el-form 
        ref="formRef"
        :model="userForm"
        :rules="rules"
        label-width="100px"
        :disabled="!isEditing"
        @validate="handleValidate"
      >
        <el-form-item :label="t('userProfile.labels.username')">
          <span>{{ userForm.username }}</span>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.age')" prop="age">
          <el-input-number v-model="userForm.age" :min="1" :max="120" />
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.gender')" prop="gender">
          <el-radio-group v-model="userForm.gender">
            <el-radio value="male">{{ t('userProfile.labels.male') }}</el-radio>
            <el-radio value="female">{{ t('userProfile.labels.female') }}</el-radio>
            <el-radio value="other">{{ t('userProfile.labels.other') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.height')" prop="height">
          <el-input-number v-model="userForm.height" :min="1" :max="300" />
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.weight')" prop="weight">
          <el-input-number v-model="userForm.weight" :min="1" :max="300" />
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.healthGoal')" prop="health_conditions">
          <el-select v-model="userForm.health_conditions" :placeholder="t('userProfile.labels.healthGoal')">
            <el-option :label="t('userProfile.options.healthGoal.weight_loss')" value="weight_loss" />
            <el-option :label="t('userProfile.options.healthGoal.weight_gain')" value="weight_gain" />
            <el-option :label="t('userProfile.options.healthGoal.maintain_health')" value="maintain_health" />
          </el-select>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.dietType')" prop="diet_type">
          <el-select v-model="userForm.diet_type" :placeholder="t('userProfile.labels.dietType')">
            <el-option :label="t('userProfile.options.dietType.normal')" value="normal" />
            <el-option :label="t('userProfile.options.dietType.vegetarian')" value="vegetarian" />
            <el-option :label="t('userProfile.options.dietType.vegan')" value="vegan" />
            <el-option :label="t('userProfile.options.dietType.low_carb')" value="low_carb" />
            <el-option :label="t('userProfile.options.dietType.keto')" value="keto" />
            <el-option :label="t('userProfile.options.dietType.paleo')" value="paleo" />
          </el-select>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.spicyLevel')" prop="spicy_level">
          <el-select v-model="userForm.spicy_level" :placeholder="t('userProfile.labels.spicyLevel')">
            <el-option :label="t('userProfile.options.spicyLevel.none')" value="none" />
            <el-option :label="t('userProfile.options.spicyLevel.mild')" value="mild" />
            <el-option :label="t('userProfile.options.spicyLevel.medium')" value="medium" />
            <el-option :label="t('userProfile.options.spicyLevel.hot')" value="hot" />
            <el-option :label="t('userProfile.options.spicyLevel.extra_hot')" value="extra_hot" />
          </el-select>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.favoriteIngredients')" prop="favorite_ingredients">
          <el-select
            v-model="userForm.favorite_ingredients"
            multiple
            filterable
            allow-create
            :placeholder="t('userProfile.labels.favoriteIngredients')"
          >
          </el-select>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.dislikedIngredients')" prop="disliked_ingredients">
          <el-select
            v-model="userForm.disliked_ingredients"
            multiple
            filterable
            allow-create
            :placeholder="t('userProfile.labels.dislikedIngredients')"
          >
          </el-select>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.cookingTime')" prop="cooking_time_preference" class="cooking-time-preference">
          <el-input-number v-model="userForm.cooking_time_preference" :min="5" :max="180" />
          <span style="margin-left: 8px;">{{ t('userProfile.labels.minutes') }}</span>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.dailyNutrition')">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="t('userProfile.labels.calories')">
                <el-input-number v-model="userForm.daily_calorie_goal" :min="0" :max="10000" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('userProfile.labels.protein')">
                <el-input-number v-model="userForm.daily_protein_goal" :min="0" :max="1000" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="t('userProfile.labels.carbs')">
                <el-input-number v-model="userForm.daily_carbs_goal" :min="0" :max="1000" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('userProfile.labels.fat')">
                <el-input-number v-model="userForm.daily_fat_goal" :min="0" :max="1000" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.targetWeight')" prop="weight_goal">
          <el-input-number v-model="userForm.weight_goal" :min="1" :max="300" />
        </el-form-item>
        
        <el-form-item :label="t('userProfile.labels.allergies')" prop="allergies">
          <el-select
            v-model="userForm.allergies"
            multiple
            filterable
            allow-create
            :placeholder="t('userProfile.labels.allergies')"
          >
            <el-option :label="t('userProfile.options.allergies.peanuts')" value="peanuts" />
            <el-option :label="t('userProfile.options.allergies.seafood')" value="seafood" />
            <el-option :label="t('userProfile.options.allergies.dairy')" value="dairy" />
            <el-option :label="t('userProfile.options.allergies.eggs')" value="eggs" />
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="isEditing">
          <el-button type="primary" @click="handleSave">{{ t('userProfile.actions.save') }}</el-button>
          <el-button @click="handleCancel">{{ t('userProfile.actions.cancel') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserProfile, updateUserProfile, getUsername } from '@/api/user'
import { useI18n } from 'vue-i18n'

const loadingManager = inject('loadingManager')
const formRef = ref(null)
const isEditing = ref(false)
const userForm = reactive({
  username: '',
  age: null,
  gender: null,
  height: null,
  weight: null,
  health_conditions: '',
  diet_type: 'normal',
  spicy_level: 'medium',
  favorite_ingredients: [],
  disliked_ingredients: [],
  cooking_time_preference: 30,
  daily_calorie_goal: null,
  daily_protein_goal: null,
  daily_carbs_goal: null,
  daily_fat_goal: null,
  weight_goal: null,
  allergies: []
})

const { t } = useI18n()

const userId = 10; // 假设 userId 是从路由或其他地方获取的

// 表单验证规则
const rules = {
  username: [
    { required: true, message: t('userProfile.rules.username.required'), trigger: 'blur' },
    { min: 2, max: 20, message: t('userProfile.rules.username.length'), trigger: 'blur' }
  ],
  age: [
    { required: true, message: t('userProfile.rules.age.required'), trigger: 'blur' },
    { type: 'number', min: 1, max: 120, message: t('userProfile.rules.age.range'), trigger: 'blur' }
  ],
  gender: [
    { required: true, message: t('userProfile.rules.gender.required'), trigger: 'change' }
  ],
  height: [
    { required: true, message: t('userProfile.rules.height.required'), trigger: 'blur' },
    { type: 'number', min: 1, max: 300, message: t('userProfile.rules.height.range'), trigger: 'blur' }
  ],
  weight: [
    { required: true, message: t('userProfile.rules.weight.required'), trigger: 'blur' },
    { type: 'number', min: 1, max: 300, message: t('userProfile.rules.weight.range'), trigger: 'blur' }
  ]
}

// 修改 fetchUserProfile 函数
const fetchUserProfile = async () => {
  loadingManager.showLoading('加载用户信息...')
  try {
    const profileResponse = await getUserProfile(userId)
    const usernameResponse = await getUsername(userId)
    
    if (profileResponse.success && usernameResponse.success) {
      const profile = profileResponse.data
      userForm.username = usernameResponse.data.username
      userForm.age = profile.age
      userForm.gender = profile.gender
      userForm.height = profile.height
      userForm.weight = profile.weight
      // 解析健康目标
      try {
        const healthConditions = JSON.parse(profile.health_conditions)
        userForm.health_conditions = healthConditions.goal || ''
      } catch (e) {
        userForm.health_conditions = ''
      }
      userForm.diet_type = profile.diet_type
      userForm.spicy_level = profile.spicy_level
      userForm.favorite_ingredients = Array.isArray(profile.favorite_ingredients) ? profile.favorite_ingredients : []
      userForm.disliked_ingredients = Array.isArray(profile.disliked_ingredients) ? profile.disliked_ingredients : []
      userForm.cooking_time_preference = profile.cooking_time_preference
      userForm.daily_calorie_goal = profile.calorie_target
      userForm.daily_protein_goal = profile.protein_target
      userForm.daily_carbs_goal = profile.carb_target
      userForm.daily_fat_goal = profile.fat_target
      userForm.weight_goal = profile.weight_goal
      userForm.allergies = Array.isArray(profile.allergies) ? profile.allergies : []
    }
  } catch (error) {
    console.error('获取用户资料失败:', error)
    ElMessage.error('加载用户信息失败')
  } finally {
    loadingManager.hideLoading()
  }
}

// 组件挂载时获取用户信息
onMounted(() => {
  fetchUserProfile() // 调用 fetchUserProfile 函数
})

// 编辑按钮点击事件
const handleEdit = () => {
  isEditing.value = true
  loadingManager.showAutoSaveTip('进入编辑模式', 'info')
}

// 表单验证反馈
const handleValidate = (prop, isValid) => {
  if (!isValid) {
    loadingManager.showAutoSaveTip('请检查输入内容', 'warning')
  }
}

// 修改 handleSave 函数
const handleSave = async () => {
  loadingManager.showLoading('保存中...')
  try {
    const data = {
      user_id: userId,
      age: Number(userForm.age),
      gender: String(userForm.gender),
      height: parseFloat(userForm.height),
      weight: parseFloat(userForm.weight),
      health_conditions: JSON.stringify({ goal: userForm.health_conditions }),
      allergies: JSON.stringify(Array.isArray(userForm.allergies) ? userForm.allergies : []),
      diet_type: String(userForm.diet_type),
      spicy_level: String(userForm.spicy_level),
      favorite_ingredients: JSON.stringify(Array.isArray(userForm.favorite_ingredients) ? userForm.favorite_ingredients : []),
      disliked_ingredients: JSON.stringify(Array.isArray(userForm.disliked_ingredients) ? userForm.disliked_ingredients : []),
      cooking_time_preference: Number(userForm.cooking_time_preference),
      calorie_target: Number(userForm.daily_calorie_goal),
      protein_target: Number(userForm.daily_protein_goal),
      carb_target: Number(userForm.daily_carbs_goal),
      fat_target: Number(userForm.daily_fat_goal),
      weight_goal: parseFloat(userForm.weight_goal)
    }
    console.log('发送的数据:', data); // 添加日志记录
    await updateUserProfile(userId, data)
    ElMessage.success('用户信息更新成功')
    isEditing.value = false
  } catch (error) {
    console.error('更新用户信息失败:', error); // 添加错误日志
    ElMessage.error('更新用户信息失败')
  } finally {
    loadingManager.hideLoading()
  }
}

// 取消按钮点击事件
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消编辑吗？未保存的修改将会丢失。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续编辑',
        type: 'warning'
      }
    )
    // 用户点击确定
    isEditing.value = false
    fetchUserProfile() // 重新获取用户信息
    loadingManager.showAutoSaveTip('已取消编辑', 'info')
  } catch {
    // 用户点击取消或关闭对话框
    loadingManager.showAutoSaveTip('继续编辑', 'info')
  }
}

// 暴露刷新方法给父组件
defineExpose({
  refresh: fetchUserProfile
})
</script>

<style scoped>
.user-profile {
  max-width: 1000px;
  margin: 0 auto;
}

.profile-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-form) {
  .el-form-item__label {
    width: 140px !important;
  }
  
  .el-form-item__content {
    margin-left: 140px !important;
  }
  
  .el-row {
    margin: 0 -10px;
    
    .el-col {
      padding: 0 10px;
      margin-bottom: 10px;
      
      .el-form-item {
        margin-bottom: 0;
        
        .el-form-item__label {
          width: auto !important;
        }
        
        .el-form-item__content {
          margin-left: 0 !important;
        }
      }
    }
  }
}

:deep(.el-card__body) {
  padding: 20px 30px;
}

:deep(.el-input),
:deep(.el-select) {
  width: 100%;
}

:deep(.el-input-number) {
  width: 180px;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

:deep(.cooking-time-preference) {
  .el-form-item__label {
    white-space: nowrap;
  }
}
</style> 