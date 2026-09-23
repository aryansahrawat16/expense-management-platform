import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { createExpense, updateExpense, getExpense } from '../api/expenses'
import { CATEGORIES } from '../constants'

const today = () => new Date().toISOString().slice(0, 10)
const empty = () => ({ title: '', amount: '', category: 'Food & Dining', date: today(), notes: '' })
const fieldCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500'

export default function AddExpense() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (isEdit) {
      getExpense(id).then(exp =>
        setForm({ title: exp.title, amount: String(exp.amount), category: exp.category, date: exp.date, notes: exp.notes || '' }))
    }
  }, [id])

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (parseFloat(form.amount) <= 0) { setError('Amount must be greater than 0'); return }
    setLoading(true)
    try {
      const payload = { ...form, amount: parseFloat(form.amount) }
      if (isEdit) await updateExpense(parseInt(id), payload)
      else await createExpense(payload)
      navigate('/expenses')
    } catch (err) {
      const d = err.response?.data?.detail
      setError(Array.isArray(d) ? d[0].msg : d || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{isEdit ? 'Edit Expense' : 'Add Expense'}</h1>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2">{error}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="title">Title</label>
            <input id="title" type="text" required value={form.title} onChange={set('title')} className={fieldCls} placeholder="e.g. Grocery run" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="amount">Amount ($)</label>
              <input id="amount" type="number" required min="0.01" step="0.01" value={form.amount} onChange={set('amount')} className={fieldCls} placeholder="0.00" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="date">Date</label>
              <input id="date" type="date" required value={form.date} onChange={set('date')} className={fieldCls} />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="category">Category</label>
            <select id="category" value={form.category} onChange={set('category')} className={fieldCls}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="notes">Notes <span className="text-gray-400 font-normal">(optional)</span></label>
            <textarea id="notes" value={form.notes} onChange={set('notes')} rows={3} className={`${fieldCls} resize-none`} placeholder="Any extra details..." />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => navigate('/expenses')}
              className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm font-medium hover:bg-gray-50 transition">
              Cancel
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg py-2 text-sm transition disabled:opacity-50">
              {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Add Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
