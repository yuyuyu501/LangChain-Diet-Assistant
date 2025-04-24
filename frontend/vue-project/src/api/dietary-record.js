import request from './request'

export const getDietaryRecords = (params) => {
  return request({
    url: '/api/dietary-records',
    method: 'get',
    params
  })
}

export const createDietaryRecord = (data) => {
  return request({
    url: '/api/dietary-records',
    method: 'post',
    data
  })
}

export const updateDietaryRecord = (id, data) => {
  return request({
    url: `/api/dietary-records/${id}`,
    method: 'put',
    data
  })
}

export const deleteDietaryRecord = (id) => {
  return request({
    url: `/api/dietary-records/${id}`,
    method: 'delete'
  })
} 