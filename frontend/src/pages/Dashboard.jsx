import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { DollarSign, Receipt, Calendar, Download, Filter, X } from 'lucide-react'
import { getDashboard, exportCSV } from '../api/expenses'
import { CATEGORIES, CHART_BLUE, inputCls, money } from '../constants'

const REFRESH_MS = 15000

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ category: '', start_date: '', end_date: '' })
  const [updatedAt, setUpdatedAt] = useState(null)

  const activeParams = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
  const paramKey = JSON.stringify(activeParams)

  useEffect(() => {
    let cancelled = false
    const refresh = () =>
      getDashboard(activeParams).then(s => {
        if (cancelled) return
        setStats(s)
        setUpdatedAt(new Date())
      }).finally(() => !cancelled && setLoading(false))

    refresh()
    const timer = setInterval(refresh, REFRESH_MS)
    const onVisible = () => document.visibilityState === 'visible' && refresh()
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      cancelled = true
      clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [paramKey])

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading...</div>
  if (!stats) return null

  const hasFilters = Object.keys(activeParams).length > 0
  const setFilter = (field) => (e) => setFilters(f => ({ ...f, [field]: e.target.value }))
  const barHeight = Math.max(120, stats.category_breakdown.length * 34)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          {updatedAt && (
            <p className="flex items-center gap-1.5 text-xs text-gray-400 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Updated {updatedAt.toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <h2 className="text-lg font-semibold text-gray-900">Breakdown</h2>
        <button onClick={() => exportCSV(activeParams)}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition text-gray-700">
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap items-center gap-3">
        <Filter size={16} className="text-gray-500" />
        <select value={filters.category} onChange={setFilter('category')} className={inputCls} aria-label="Category">
          <option value="">All Categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input type="date" aria-label="From date" value={filters.start_date} onChange={setFilter('start_date')} className={inputCls} />
        <span className="text-gray-400 text-sm">to</span>
        <input type="date" aria-label="To date" value={filters.end_date} onChange={setFilter('end_date')} className={inputCls} />
        {hasFilters && (
          <button onClick={() => setFilters({ category: '', start_date: '', end_date: '' })}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500">
            <X size={14} /> Clear
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard icon={DollarSign} label="Total Spent" value={money(stats.total_spent)} color="bg-sky-500" />
        <StatCard icon={Calendar} label="This Month" value={money(stats.total_this_month)} color="bg-indigo-500" />
        <StatCard icon={Receipt} label="Total Expenses" value={stats.total_expenses} color="bg-emerald-500" />
      </div>

      {stats.category_breakdown.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <Receipt size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">{hasFilters ? 'No expenses match these filters' : 'No expenses yet'}</p>
          <p className="text-sm mt-1">{hasFilters ? 'Try a different category or date range' : 'Add an expense and it will show up here'}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-800 mb-4">Spending by Category</h2>
            <ResponsiveContainer width="100%" height={barHeight}>
              <BarChart data={stats.category_breakdown} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid horizontal={false} stroke="#eceae6" />
                <XAxis type="number" tick={{ fontSize: 12, fill: '#52514e' }} axisLine={false} tickLine={false}
                  tickFormatter={(v) => `$${v}`} />
                <YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 12, fill: '#0b0b0b' }}
                  axisLine={false} tickLine={false} />
                <Tooltip formatter={(v) => [money(v), 'Spent']} cursor={{ fill: '#f3f2ef' }} />
                <Bar dataKey="total" fill={CHART_BLUE} radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-800 mb-4">Category Breakdown</h2>
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-500 text-left">
                <tr><th className="pb-2 font-medium">Category</th><th className="pb-2 font-medium">Expenses</th><th className="pb-2 font-medium text-right">Total</th></tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {stats.category_breakdown.map(c => (
                  <tr key={c.category}>
                    <td className="py-2.5 font-medium text-gray-700">{c.category}</td>
                    <td className="py-2.5 text-gray-500">{c.count}</td>
                    <td className="py-2.5 text-right font-semibold text-gray-900">{money(c.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
