import client from './client'

const data = (r) => r.data

export const getBudgets = () => client.get('/budgets/').then(data)
export const saveBudget = (category, monthly_limit) =>
  client.put('/budgets/', { category, monthly_limit }).then(data)
export const deleteBudget = (id) => client.delete(`/budgets/${id}`)

export const getTrends = (months = 6) => client.get('/insights/trends', { params: { months } }).then(data)
