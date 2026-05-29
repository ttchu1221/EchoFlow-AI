import { useState } from 'react'
import toast from 'react-hot-toast'
import { HiOutlineWrenchScrewdriver, HiOutlineSparkles, HiOutlineArrowTrendingUp, HiOutlineCheckCircle } from 'react-icons/hi2'
import { optimizeTitle } from '../api/client'

export default function OptimizePanel({ platforms }) {
  const [form, setForm] = useState({
    title: '',
    platform: 'xiaohongshu',
    optimize_count: 3,
    llm_provider: null,
  })
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) {
      toast.error('请输入要优化的标题')
      return
    }
    setLoading(true)
    setResults(null)
    try {
      const data = await optimizeTitle({
        ...form,
        title: form.title.trim(),
      })
      setResults(data)
      toast.success(`生成了 ${(data.optimized_options || data.optimized || []).length} 个优化方案！`)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 输入表单 */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            原始标题 <span className="text-red-400">*</span>
          </label>
          <textarea
            value={form.title}
            onChange={(e) => setForm(prev => ({ ...prev, title: e.target.value }))}
            placeholder="输入你想要优化的标题..."
            rows={2}
            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all text-gray-800 placeholder:text-gray-400 resize-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select
              value={form.platform}
              onChange={(e) => setForm(prev => ({ ...prev, platform: e.target.value }))}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all bg-white text-gray-800"
            >
              {platforms.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">优化方案数</label>
            <select
              value={form.optimize_count}
              onChange={(e) => setForm(prev => ({ ...prev, optimize_count: Number(e.target.value) }))}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all bg-white text-gray-800"
            >
              {[2, 3, 5].map(n => (
                <option key={n} value={n}>{n} 个</option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-gradient-to-r from-accent-500 to-pink-600 text-white font-medium shadow-lg shadow-accent-200 hover:shadow-xl hover:from-accent-600 hover:to-pink-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              AI 正在优化...
            </>
          ) : (
            <>
              <HiOutlineWrenchScrewdriver className="w-5 h-5" />
              优化标题
            </>
          )}
        </button>
      </form>

      {/* 加载 */}
      {loading && (
        <div className="space-y-4">
          {Array.from({ length: form.optimize_count }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl p-5 border border-gray-100">
              <div className="shimmer h-6 w-3/4 rounded-lg mb-3" />
              <div className="shimmer h-4 w-1/2 rounded-lg" />
            </div>
          ))}
        </div>
      )}

      {/* 结果 */}
      {results && !loading && (
        <div>
          {/* 原始标题 */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4 border border-gray-200">
            <p className="text-xs text-gray-500 mb-1">原始标题</p>
            <p className="font-medium text-gray-700">{results.original_title}</p>
          </div>

          <div className="flex items-center gap-2 mb-4">
            <HiOutlineSparkles className="w-5 h-5 text-accent-500" />
            <h3 className="font-semibold text-gray-800">
              {(results.optimized_options || results.optimized || []).length} 个优化方案
            </h3>
          </div>

          <div className="space-y-4">
            {(results.optimized_options || results.optimized || []).map((item, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-gray-100 p-5 card-hover">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <h4 className="text-base font-semibold text-gray-800 leading-relaxed">
                    {item.title}
                  </h4>
                  <span className={`flex-shrink-0 px-2.5 py-1 rounded-lg text-sm font-semibold ${
                    (item.predicted_heat || 0) >= 7
                      ? 'text-green-700 bg-green-50'
                      : (item.predicted_heat || 0) >= 5
                      ? 'text-yellow-700 bg-yellow-50'
                      : 'text-gray-700 bg-gray-50'
                  }`}>
                    热度 {(item.predicted_heat || 0).toFixed(1)}
                  </span>
                </div>

                {/* 改进点 */}
                <div className="space-y-1.5">
                  {(item.changes || item.improvements || []).map((imp, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <HiOutlineCheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span>{imp}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
