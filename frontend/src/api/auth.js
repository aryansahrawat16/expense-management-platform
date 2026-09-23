import client from './client'

export const login = async (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('token', res.data.access_token)
  return res.data
}

export const register = async (name, email, password) => {
  const res = await client.post('/auth/register', { name, email, password })
  return res.data
}

export const getMe = () => client.get('/auth/me').then(r => r.data)

export const logout = () => localStorage.removeItem('token')
