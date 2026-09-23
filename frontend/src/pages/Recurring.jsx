import { useEffect, useState } from 'react'
import { Pause, Play, Trash2, Repeat } from 'lucide-react'
import { getRecurring, createRecurring, updateRecurring, deleteRecurring } from '../api/features'
import { CATEGORIES, CATEGORY_COLORS, inputCls, money } from '../constants'

const today = () => new Date().toISOString().slice(0, 10)
const empty = { title: '', amount: '', category: 'Entertainment', frequency: 'monthly', start_date: today(), notes: '' }
const FREQ_LABEL = { weekly: 'Every week', monthly: 'Every month', yearly: 'Every year' }

const errorText = (err) => {
  const d = err.response?.data?.detail
  return Array.isArray(d) ? d.map(x => x.msg.replace('Value error, ', '')).join('. ') : d || 'Something went wrong'
}

export default function Recurring() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const load = () => getRecurring().then(setItems).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await createRecurring({ ...form, amount: parseFloat(form.amount) })
      setForm({ ...empty, start_date: today() })
      await load()
    } catch (err) {
      setError(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  const toggle = async (r) => {
    const updated = await updateRecurring(r.id, { active: !r.active })
    setItems(prev => prev.map(x => (x.id === r.id ? updated : x)))
  }

  const remove = async (r) => {
    await deleteRecurring(r.id)
    setItems(prev => prev.filter(x => x.id !== r.id))
  }

  const monthlyCost = items.filter(r => r.active).reduce((sum, r) =>
    sum + (r.frequency === 'weekly' ? r.amount * 52 / 12 : r.frequency === 'yearly' ? r.amount / 12 : r.amount), 0)

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Recurring Expenses</h1>
        <p className="text-sm text-gray-500 mt-1">
          Subscriptions, rent and other bills that repeat. They get added to your expenses on their due date.
        </p>
      </div>

      <form onSubmit={handleCreate} className="bg-white rounded-xl border border-gray-200 p-5 grid grid-cols-1 sm:grid-cols-6 gap-3">
        <label className="sm:col-span-2 flex flex-col gap-1 text-sm font-medium text-gray-700">
          Name
          <input required value={form.title} onChange={set('title')} placeholder="Spotify" className={inputCls} />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">
          Amount ($)
          <input type="number" required min="0.01" step="0.01" value={form.amount} onChange={set('amount')} placeholder="11.99" className={inputCls} />
        </label>
        <label className="sm:col-span-3 flex flex-col gap-1 text-sm font-medium text-gray-700">
          Category
          <select value={form.category} onChange={set('category')} className={inputCls}>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="sm:col-span-2 flex flex-col gap-1 text-sm font-medium text-gray-700">
          How often
          <select value={form.frequency} onChange={set('frequency')} className={inputCls}>
            {Object.entries(FREQ_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label className="sm:col-span-2 flex flex-col gap-1 text-sm font-medium text-gray-700">
          First charge
          <input type="date" required value={form.start_date} onChange={set('start_date')} className={inputCls} />
        </label>
        <div className="sm:col-span-2 flex items-end">
          <button type="submit" disabled={saving}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg px-4 py-2 text-sm transition disabled:opacity-50">
            {saving ? 'Adding...' : 'Add recurring'}
          </button>
        </div>
        {error && <p className="sm:col-span-6 text-sm text-red-600">{error}</p>}
      </form>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {items.length > 0 && (
          <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 text-sm text-gray-600">
            Active recurring costs: about <span className="font-semibold text-gray-900">{money(monthlyCost)}</span> per month
          </div>
        )}
        {loading ? (
          <p className="p-6 text-sm text-gray-400">Loading...</p>
        ) : items.length === 0 ? (
          <div className="p-10 text-center text-gray-400">
            <Repeat size={36} className="mx-auto mb-2 opacity-30" />
            <p className="font-medium">No recurring expenses yet</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {items.map(r => (
              <li key={r.id} className={`flex flex-wrap items-center gap-3 px-5 py-3 ${r.active ? '' : 'opacity-60'}`}>
                <div className="flex-1 min-w-[10rem]">
                  <p className="font-medium text-gray-900">{r.title}</p>
                  <p className="text-xs text-gray-500">
                    {FREQ_LABEL[r.frequency]}, {r.active ? `next on ${r.next_date}` : 'paused'}
                  </p>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLORS[r.category]}`}>{r.category}</span>
                <span className="w-20 text-right font-semibold text-gray-900">{money(r.amount)}</span>
                <button onClick={() => toggle(r)} aria-label={r.active ? `Pause ${r.title}` : `Resume ${r.title}`}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-sky-600 hover:bg-sky-50 transition">
                  {r.active ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <button onClick={() => remove(r)} aria-label={`Delete ${r.title}`}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition">
                  <Trash2 size={16} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="text-xs text-gray-400">Deleting a recurring expense stops future charges. Charges already added stay in your expense history.</p>
    </div>
  )
}
