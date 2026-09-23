import { useEffect, useState } from 'react'
import { getExpenses, deleteExpense, exportCSV } from '../api/expenses'
import { Trash2, Pencil, Download, Filter, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { CATEGORIES, CATEGORY_COLORS } from '../constants'

export default function Expenses() {
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ category: '', start_date: '', end_date: '' })
  const [applied, setApplied] = useState({})
  const [deleting, setDeleting] = useState(null)

  const load = (params) => {
    setLoading(true)
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v))
    getExpenses(clean).then(setExpenses).finally(() => setLoading(false))
  }

  useEffect(() => { load({}) }, [])

  const applyFilters = () => {
    setApplied(filters)
    load(filters)
  }

  const clearFilters = () => {
    const empty = { category: '', start_date: '', end_date: '' }
    setFilters(empty)
    setApplied(empty)
    load(empty)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this expense?')) return
    setDeleting(id)
    await deleteExpense(id)
    setExpenses(prev => prev.filter(e => e.id !== id))
    setDeleting(null)
  }

  const handleExport = () => {
    const clean = Object.fromEntries(Object.entries(applied).filter(([, v]) => v))
    exportCSV(clean)
  }

  const hasFilters = Object.values(applied).some(Boolean)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Expenses</h1>
        <div className="flex gap-2">
          <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition text-gray-700">
            <Download size={16} /> Export CSV
          </button>
          <Link to="/add" className="flex items-center gap-2 px-4 py-2 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition font-medium">
            + Add Expense
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter size={16} className="text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filter</span>
          {hasFilters && (
            <button onClick={clearFilters} className="ml-auto flex items-center gap-1 text-xs text-gray-500 hover:text-red-500">
              <X size={14} /> Clear
            </button>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <select
            value={filters.category}
            onChange={e => setFilters(f => ({ ...f, category: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="date" value={filters.start_date} onChange={e => setFilters(f => ({ ...f, start_date: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
          <input type="date" value={filters.end_date} onChange={e => setFilters(f => ({ ...f, end_date: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
          <button onClick={applyFilters} className="bg-sky-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-sky-700 transition">
            Apply
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        ) : expenses.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="font-medium">No expenses found</p>
            <p className="text-sm mt-1">{hasFilters ? 'Try adjusting your filters' : 'Add your first expense!'}</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
              <tr>
                <th className="px-4 py-3 text-left">Title</th>
                <th className="px-4 py-3 text-left">Category</th>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-right">Amount</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {expenses.map(e => (
                <tr key={e.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{e.title}</div>
                    {e.notes && <div className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{e.notes}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLORS[e.category] || 'bg-gray-100 text-gray-600'}`}>
                      {e.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{e.date}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">${e.amount.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/edit/${e.id}`} className="p-1.5 rounded-lg text-gray-400 hover:text-sky-600 hover:bg-sky-50 transition">
                        <Pencil size={15} />
                      </Link>
                      <button onClick={() => handleDelete(e.id)} disabled={deleting === e.id}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-40">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td colSpan={3} className="px-4 py-3 text-sm text-gray-500 font-medium">
                  {expenses.length} expense{expenses.length !== 1 ? 's' : ''}
                </td>
                <td className="px-4 py-3 text-right font-bold text-gray-900">
                  ${expenses.reduce((s, e) => s + e.amount, 0).toFixed(2)}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </div>
  )
}
