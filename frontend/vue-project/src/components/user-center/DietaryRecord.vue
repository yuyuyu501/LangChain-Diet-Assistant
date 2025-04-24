<template>
  <div class="dietary-record">
    <el-card class="record-card">
      <template #header>
        <div class="card-header">
          <span>饮食记录</span>
          <el-button-group>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>添加记录
            </el-button>
            <el-button type="success" @click="refreshRecords">
              <el-icon><Refresh /></el-icon>刷新
            </el-button>
          </el-button-group>
        </div>
      </template>

      <el-date-picker
        v-model="selectedDate"
        type="date"
        placeholder="选择日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        @change="handleDateChange"
        style="margin-bottom: 20px;"
      />

      <div v-if="!records.length" class="empty-state">
        暂无饮食记录
      </div>

      <div v-else class="records-list">
        <el-timeline>
          <el-timeline-item
            v-for="record in records"
            :key="record.id"
            :timestamp="formatTime(record.recorded_at)"
            :type="getMealTypeColor(record.meal_type)"
          >
            <el-card class="record-item">
              <template #header>
                <div class="record-header">
                  <span class="meal-type">{{ getMealTypeLabel(record.meal_type) }}</span>
                  <div class="actions">
                    <el-button-group>
                      <el-button
                        type="primary"
                        link
                        @click="handleEdit(record)"
                      >
                        编辑
                      </el-button>
                      <el-button
                        type="danger"
                        link
                        @click="handleDelete(record.id)"
                      >
                        删除
                      </el-button>
                    </el-button-group>
                  </div>
                </div>
              </template>

              <div class="record-content">
                <div class="food-items">
                  <h4>食物清单：</h4>
                  <el-tag
                    v-for="item in processedFoodItems(record.food_items)"
                    :key="item"
                    class="food-tag"
                  >
                    {{ item }}
                  </el-tag>
                </div>

                <div class="notes" v-if="record.notes">
                  <h4>备注：</h4>
                  <p>{{ record.notes }}</p>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <!-- 添加/编辑记录对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑记录' : '添加记录'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="recordForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用餐类型" prop="meal_type">
          <el-select v-model="recordForm.meal_type" placeholder="请选择用餐类型">
            <el-option label="早餐" value="早餐" />
            <el-option label="午餐" value="午餐" />
            <el-option label="晚餐" value="晚餐" />
            <el-option label="加餐" value="加餐" />
          </el-select>
        </el-form-item>

        <el-form-item label="用餐时间" prop="recorded_at">
          <el-time-picker
            v-model="recordForm.recorded_at"
            format="HH:mm"
            placeholder="选择时间"
          />
        </el-form-item>

        <el-form-item label="食物清单" prop="food_items">
          <el-select
            v-model="recordForm.food_items"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入食物名称"
          >
            <el-option
              v-for="item in commonFoods"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="recordForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { 
  getDietaryRecords,
  createDietaryRecord,
  updateDietaryRecord,
  deleteDietaryRecord
} from '@/api/dietary-record'
import { storage } from '@/utils/storage'

// 常用食物列表
const commonFoods = [
  '米饭', '面包', '牛奶', '鸡蛋', '水果', '蔬菜',
  '牛肉', '鸡肉', '鱼', '豆腐', '玉米', '燕麦'
]

const selectedDate = ref(new Date().toISOString().split('T')[0])
const records = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref(null)

// 表单数据
const recordForm = reactive({
  user_id: Number(storage.getUser().user_id),  // 确保 user_id 是数字类型
  meal_type: '早餐',
  food_items: [],  // 初始化为空数组
  calories: 0,
  protein: 0,
  carbs: 0,
  fat: 0,
  satisfaction: 3,
  notes: '',
  recorded_at: new Date()  // 初始化为当前时间
})

// 表单验证规则
const rules = {
  meal_type: [
    { required: true, message: '请选择用餐类型', trigger: 'change' }
  ],
  recorded_at: [
    { required: true, message: '请选择用餐时间', trigger: 'change' }
  ],
  food_items: [
    { required: true, message: '请至少输入一个食物', trigger: 'change' }
  ]
}

const emit = defineEmits(['recordAdded'])

// 获取饮食记录
const fetchRecords = async () => {
  try {
    const response = await getDietaryRecords({ date: selectedDate.value })
    if (response.success) {
      records.value = response.data
    } else {
      ElMessage.error(response.message || '获取饮食记录失败')
    }
  } catch (error) {
    console.error('获取饮食记录失败:', error)
    ElMessage.error('获取饮食记录失败')
  }
}

// 处理日期变化
const handleDateChange = () => {
  fetchRecords()
}

// 刷新记录
const refreshRecords = () => {
  fetchRecords()
}

// 显示添加对话框
const showAddDialog = () => {
  isEditing.value = false
  resetForm()
  dialogVisible.value = true
}

// 处理编辑
const handleEdit = (record) => {
  isEditing.value = true
  Object.assign(recordForm, record)
  dialogVisible.value = true
}

// 处理删除
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
      type: 'warning'
    })
    await deleteDietaryRecord(id)
    ElMessage.success('删除成功')
    fetchRecords()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 处理时间格式
        const timeStr = recordForm.recorded_at.toTimeString().split(' ')[0].substring(0, 5)
        const formData = {
          user_id: Number(storage.getUser().user_id),
          meal_type: recordForm.meal_type,
          food_items: JSON.stringify(recordForm.food_items), // 确保food_items是JSON格式
          calories: 0,
          protein: 0,
          carbs: 0,
          fat: 0,
          satisfaction: 3,
          notes: recordForm.notes,
          recorded_at: `${selectedDate.value} ${timeStr}`
        }

        let response;
        if (isEditing.value && recordForm.id) {
          // 确保在编辑时调用 updateDietaryRecord
          response = await updateDietaryRecord(recordForm.id, formData);
        } else {
          response = await createDietaryRecord(formData);
        }
        
        if (response && response.success) {
          ElMessage.success('记录成功');
          dialogVisible.value = false;
          fetchRecords(); // 刷新记录列表
        } else {
          ElMessage.error(response.message || '操作失败');
        }
      } catch (error) {
        console.error('操作失败:', error);
        ElMessage.error('操作失败');
      }
    }
  });
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  return time.substring(11, 16)
}

// 获取用餐类型标签
const getMealTypeLabel = (type) => {
  return type || '其他'  // 直接返回类型，因为后端已经返回中文
}

// 获取用餐类型颜色
const getMealTypeColor = (type) => {
  switch (type) {
    case '早餐':
      return 'primary'
    case '午餐':
      return 'success'
    case '晚餐':
      return 'warning'
    case '加餐':
      return 'info'
    default:
      return ''
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(recordForm, {
    user_id: Number(storage.getUser().user_id),
    meal_type: '早餐',
    food_items: [],
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0,
    satisfaction: 3,
    notes: '',
    recorded_at: new Date()
  })
}

// 组件挂载时获取数据
onMounted(() => {
  fetchRecords()
})

// 暴露刷新方法给父组件
defineExpose({
  refresh: refreshRecords
})

const processedFoodItems = (foodItems) => {
  try {
    // 去掉除逗号以外的所有符号
    const cleanedItems = foodItems.replace(/[^,\u4e00-\u9fa5,]/g, '');
    // 以逗号为分隔符分割字符串
    return cleanedItems.split(',').filter(item => item.trim() !== ''); // 过滤掉空项
  } catch (error) {
    console.error('解析食物清单失败:', error);
    return []; // 返回空数组以防止渲染错误
  }
}
</script>

<style scoped>
.dietary-record {
  max-width: 800px;
  margin: 0 auto;
}

.record-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.record-item {
  margin-bottom: 10px;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meal-type {
  font-weight: bold;
  color: #303133;
}

.record-content {
  padding: 10px 0;
}

.food-items {
  margin-bottom: 15px;
}

.food-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.notes {
  h4 {
    margin: 10px 0;
    color: #303133;
  }
  
  p {
    margin: 0;
    color: #606266;
    line-height: 1.6;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 