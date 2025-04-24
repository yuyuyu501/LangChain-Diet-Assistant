import request from './request'

export const getHealthAdvices = (params) => {
  return request({
    url: '/api/health-advice',
    method: 'get',
    params: {
      ...params,
      favorites_only: false
    }
  })
}

export const getFavoriteAdvices = (params) => {
  return request({
    url: '/api/health-advice',
    method: 'get',
    params: {
      ...params,
      favorites_only: true
    }
  })
}

export const updateAdviceRating = (id, rating) => {
  return request({
    url: `/api/health-advice/${id}/rating`,
    method: 'put',
    data: { rating }
  })
}

export const toggleAdviceFavorite = (id) => {
  return request({
    url: `/api/health-advice/${id}/favorite`,
    method: 'put'
  })
}

export const updateAdviceFeedback = (id, feedback) => {
  return request({
    url: `/api/health-advice/${id}/feedback`,
    method: 'put',
    data: { feedback }
  })
}

export const deleteHealthAdvice = (id) => {
  return request({
    url: `/api/health-advice/${id}`,
    method: 'delete'
  })
} 