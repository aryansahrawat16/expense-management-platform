import client from './client'

export const getDashboard = (params = {}) =>
  client.get('/expenses/dashboard', { params }).then(r => r.data)

export const getExpenses = (params = {}) =>
  client.get('/expenses/', { params }).then(r => r.data)

export const createExpense = (data) => client.post('/expenses/', data).then(r => r.data)

export const updateExpense = (id, data) => client.put(`/expenses/${id}`, data).then(r => r.data)

export const deleteExpense = (id) => client.delete(`/expenses/${id}`)

export const exportCSV = (params = {}) => {
  const token = localStorage.getItem('token')
  const query = new URLSearchParams(params).toString()
  const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/expenses/export/csv${query ? '?' + query : ''}`
  const a = document.createElement('a')
  a.href = url
  a.download = 'expenses.csv'
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then(res => res.blob())
    .then(blob => {
      const blobUrl = URL.createObjectURL(blob)
      a.href = blobUrl
      a.click()
      URL.revokeObjectURL(blobUrl)
    })
}

export const getExpense = (id) => client.get(`/expenses/${id}`).then(r => r.data)
