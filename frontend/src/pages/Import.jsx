import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText } from 'lucide-react'
import { previewImport, commitImport } from '../api/features'
import { CATEGORIES, money } from '../constants'

const SOURCE_BADGE = {
  history: { text: 'Learned', title: 'You used this category for this merchant before', cls: 'bg-emerald-50 text-emerald-700' },
  keyword: { text: 'Matched', title: 'Matched a known merchant keyword', cls: 'bg-sky-50 text-sky-700' },
  default: { text: 'Guess', title: 'No match found - please check', cls: 'bg-gray-100 text-gray-600' },
  manual: { text: 'You chose', title: 'Set by you', cls: 'bg-violet-50 text-violet-700' },
}

export default function Import() {
  const [preview, setPreview] = useState(null)
  const [rows, setRows] = useState([])
  const [fileName, setFileName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  const handleFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    setBusy(true)
    setFileName(file.name)
    try {
      const p = await previewImport(file)
      setPreview(p)
      setRows(p.rows.map(r => ({ ...r, include: !r.duplicate })))
    } catch (err) {
      setPreview(null)
      setError(err.response?.data?.detail || 'Could not read that file')
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  const update = (i, patch) => setRows(prev => prev.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const selected = rows.filter(r => r.include)

  const handleImport = async () => {
    setBusy(true)
    try {
      await commitImport(selected.map(({ title, amount, date, category }) => ({ title, amount, date, category, notes: 'Imported' })))
      navigate('/expenses')
    } catch (err) {
      setError('Import failed. Nothing was saved.')
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Import Bank Statement</h1>
        <p className="text-sm text-gray-500 mt-1">
          Download a CSV from your bank's website and upload it here. Deposits and refunds get skipped,
          and nothing is saved until you check it over and hit Import.
        </p>
      </div>

      <label className="flex flex-col items-center justify-center gap-2 bg-white border-2 border-dashed border-gray-300 rounded-xl p-8 cursor-pointer hover:border-sky-400 hover:bg-sky-50/40 transition">
        <Upload size={28} className="text-gray-400" />
        <span className="text-sm font-medium text-gray-700">{busy && !preview ? 'Reading file...' : 'Choose a CSV file'}</span>
        <span className="text-xs text-gray-400">Max 2 MB, up to 2,000 transactions</span>
        <input type="file" accept=".csv,text/csv" onChange={handleFile} className="sr-only" />
      </label>

      {error && <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2">{error}</div>}

      {preview && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 border-b border-gray-100">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <FileText size={16} />
              <span className="font-medium text-gray-800">{fileName}</span>
              <span>- {preview.rows.length} expenses found, {preview.skipped} skipped ({preview.detected_format})</span>
            </div>
            <button onClick={handleImport} disabled={busy || selected.length === 0}
              className="bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg px-4 py-2 text-sm transition disabled:opacity-50">
              {busy ? 'Importing...' : `Import ${selected.length} expense${selected.length !== 1 ? 's' : ''} (${money(selected.reduce((s, r) => s + r.amount, 0))})`}
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
                <tr>
                  <th className="px-4 py-2 w-10">
                    <input type="checkbox" aria-label="Select all" checked={selected.length === rows.length && rows.length > 0}
                      onChange={e => setRows(prev => prev.map(r => ({ ...r, include: e.target.checked })))} />
                  </th>
                  <th className="px-4 py-2 text-left">Date</th>
                  <th className="px-4 py-2 text-left">Description</th>
                  <th className="px-4 py-2 text-left">Category</th>
                  <th className="px-4 py-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((r, i) => {
                  const badge = SOURCE_BADGE[r.category_source]
                  return (
                    <tr key={i} className={r.include ? '' : 'opacity-50'}>
                      <td className="px-4 py-2 text-center">
                        <input type="checkbox" checked={r.include} onChange={e => update(i, { include: e.target.checked })}
                          aria-label={`Include ${r.title}`} />
                      </td>
                      <td className="px-4 py-2 text-gray-500 whitespace-nowrap">{r.date}</td>
                      <td className="px-4 py-2">
                        <span className="font-medium text-gray-900">{r.title}</span>
                        {r.duplicate && <span className="ml-2 text-xs text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">Possible duplicate</span>}
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          <select value={r.category} aria-label={`Category for ${r.title}`}
                            onChange={e => update(i, { category: e.target.value, category_source: 'manual' })}
                            className="border border-gray-300 rounded-md px-2 py-1 text-sm">
                            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                          </select>
                          <span title={badge.title} className={`text-xs px-1.5 py-0.5 rounded ${badge.cls}`}>{badge.text}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-gray-900">{money(r.amount)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
