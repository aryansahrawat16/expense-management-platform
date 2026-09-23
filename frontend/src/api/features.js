import client from './client'

const data = (r) => r.data

export const getBudgets = () => client.get('/budgets/').then(data)
export const saveBudget = (category, monthly_limit) =>
  client.put('/budgets/', { category, monthly_limit }).then(data)
export const deleteBudget = (id) => client.delete(`/budgets/${id}`)

export const getTrends = (months = 6) => client.get('/insights/trends', { params: { months } }).then(data)

export const getRecurring = () => client.get('/recurring/').then(data)
export const createRecurring = (body) => client.post('/recurring/', body).then(data)
export const updateRecurring = (id, body) => client.patch(`/recurring/${id}`, body).then(data)
export const deleteRecurring = (id) => client.delete(`/recurring/${id}`)
