import { useEffect, useState } from 'react'
import { getBudgets, saveBudget, deleteBudget } from '../api/features'
import { CATEGORIES, inputCls } from '../constants'
import BudgetBars from '../components/BudgetBars'

export default function Budgets() {
  const [budgets, setBudgets] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState(CATEGORIES[0])
  const [limit, setLimit] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => { getBudgets().then(setBudgets).finally(() => setLoading(false)) }, [])

  const existing = budgets.find(b => b.category === category)

  const handleSave = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      setBudgets(await saveBudget(category, parseFloat(limit)))
      setLimit('')
    } catch (err) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Could not save budget')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (b) => {
    await deleteBudget(b.id)
    setBudgets(prev => prev.filter(x => x.id !== b.id))
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Budgets</h1>
        <p className="text-sm text-gray-500 mt-1">
          Set a monthly limit per category. You'll get a warning at 80% and an alert when you go over. Limits reset on the 1st of each month.
        </p>
      </div>

      <form onSubmit={handleSave} className="bg-white rounded-xl border border-gray-200 p-5 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">
          Category
          <select value={category} onChange={e => setCategory(e.target.value)} className={inputCls}>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">
          Monthly limit ($)
          <input type="number" required min="1" step="0.01" value={limit} onChange={e => setLimit(e.target.value)}
            placeholder={existing ? String(existing.monthly_limit) : '200'} className={`${inputCls} w-36`} />
        </label>
        <button type="submit" disabled={saving}
          className="bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg px-4 py-2 text-sm transition disabled:opacity-50">
          {saving ? 'Saving...' : existing ? 'Update budget' : 'Add budget'}
        </button>
        {error && <p className="w-full text-sm text-red-600">{error}</p>}
      </form>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {loading ? (
          <p className="text-gray-400 text-sm">Loading...</p>
        ) : budgets.length === 0 ? (
          <p className="text-gray-500 text-sm">No budgets yet. Add one above to start tracking.</p>
        ) : (
          <BudgetBars budgets={budgets} onDelete={handleDelete} />
        )}
      </div>
    </div>
  )
}
