import { useLocalStorage } from '@vueuse/core'

class LocalDataManager {
  constructor() {
    // 初始化本地存储
    this.messages = useLocalStorage('local_messages', [])
    this.advice = useLocalStorage('local_advice', [])
    this.dietRecords = useLocalStorage('local_diet_records', [])
    this.syncStatus = useLocalStorage('sync_status', {
      lastSync: null,
      pendingChanges: {
        messages: [],
        advice: [],
        dietRecords: []
      }
    })
  }

  // 添加消息记录
  addMessage(message) {
    message.sync_status = 'pending'
    this.messages.value.push(message)
    this.addPendingChange('messages', message)
  }

  // 添加健康建议
  addAdvice(advice) {
    advice.sync_status = 'pending'
    this.advice.value.push(advice)
    this.addPendingChange('advice', advice)
  }

  // 添加饮食记录
  addDietRecord(record) {
    record.sync_status = 'pending'
    this.dietRecords.value.push(record)
    this.addPendingChange('dietRecords', record)
  }

  // 添加待同步的变更
  addPendingChange(type, data) {
    this.syncStatus.value.pendingChanges[type].push({
      data,
      timestamp: new Date().toISOString()
    })
  }

  // 获取待同步的数据
  getPendingChanges() {
    return {
      messages: this.syncStatus.value.pendingChanges.messages,
      advice: this.syncStatus.value.pendingChanges.advice,
      dietRecords: this.syncStatus.value.pendingChanges.dietRecords
    }
  }

  // 清除已同步的数据
  clearSyncedData(type, ids) {
    if (type === 'messages') {
      this.messages.value = this.messages.value.filter(m => !ids.includes(m.record_id))
    } else if (type === 'advice') {
      this.advice.value = this.advice.value.filter(a => !ids.includes(a.id))
    } else if (type === 'dietRecords') {
      this.dietRecords.value = this.dietRecords.value.filter(r => !ids.includes(r.record_id))
    }

    // 清除待同步记录
    this.syncStatus.value.pendingChanges[type] = 
      this.syncStatus.value.pendingChanges[type].filter(
        change => !ids.includes(change.data.id || change.data.record_id)
      )
  }

  // 更新同步状态
  updateSyncStatus(timestamp) {
    this.syncStatus.value.lastSync = timestamp
  }

  // 获取未同步的数据数量
  getUnsyncedCount() {
    return {
      messages: this.syncStatus.value.pendingChanges.messages.length,
      advice: this.syncStatus.value.pendingChanges.advice.length,
      dietRecords: this.syncStatus.value.pendingChanges.dietRecords.length
    }
  }

  // 处理同步冲突
  handleConflict(conflict) {
    const { table, recordId, resolution, serverData, clientData } = conflict
    
    let type
    if (table === 'chat_records') type = 'messages'
    else if (table === 'health_advice') type = 'advice'
    else if (table === 'dietary_records') type = 'dietRecords'
    
    if (resolution === 'keep_server') {
      // 使用服务器数据替换本地数据
      this.updateLocalData(type, recordId, serverData)
    } else if (resolution === 'keep_client') {
      // 保持本地数据不变，只更新同步状态
      this.updateSyncStatus(new Date().toISOString())
    } else if (resolution === 'merge') {
      // 合并数据
      const mergedData = this.mergeData(type, serverData, clientData)
      this.updateLocalData(type, recordId, mergedData)
    }
  }

  // 更新本地数据
  updateLocalData(type, id, data) {
    if (type === 'messages') {
      const index = this.messages.value.findIndex(m => m.record_id === id)
      if (index !== -1) {
        this.messages.value[index] = { ...data, sync_status: 'synced' }
      }
    } else if (type === 'advice') {
      const index = this.advice.value.findIndex(a => a.id === id)
      if (index !== -1) {
        this.advice.value[index] = { ...data, sync_status: 'synced' }
      }
    } else if (type === 'dietRecords') {
      const index = this.dietRecords.value.findIndex(r => r.record_id === id)
      if (index !== -1) {
        this.dietRecords.value[index] = { ...data, sync_status: 'synced' }
      }
    }
  }

  // 合并数据
  mergeData(type, serverData, clientData) {
    if (type === 'messages') {
      // 聊天记录通常不需要合并，使用最新的数据
      return clientData.timestamp > serverData.timestamp ? clientData : serverData
    } else if (type === 'advice') {
      // 合并健康建议
      return {
        ...serverData,
        content: `${serverData.content}\n---\n${clientData.content}`,
        symptoms: `${serverData.symptoms}\n---\n${clientData.symptoms}`,
        is_favorite: serverData.is_favorite || clientData.is_favorite,
        rating: Math.max(serverData.rating || 0, clientData.rating || 0),
        sync_status: 'synced'
      }
    } else if (type === 'dietRecords') {
      // 饮食记录通常不需要合并，使用最新的数据
      return clientData.timestamp > serverData.timestamp ? clientData : serverData
    }
    return clientData
  }
}

export const localDataManager = new LocalDataManager() 