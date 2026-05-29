import { useState } from 'react'
import toast from 'react-hot-toast'
import { HiOutlineRocketLaunch, HiOutlineClipboardDocument, HiOutlineSparkles } from 'react-icons/hi2'
import { generateTitles } from '../api/client'
import TitleCard from './TitleCard'

export default function GeneratePanel({ platforms }) {
  const [form, setForm] = useState({
    topic: '',
    platform: 'xiaohongshu',
    creator_profile: '',
    count: 5,
    hook_types: [],
    llm_provider: null,
  })
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const currentPlatform = platforms.find(p => p.id === form.platform)
  const hookTypes = currentPlatform?.hook_types || []

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.topic.trim()) {
      toast.error('请输入选题')
      return
    }
    setLoading(true)
    setResults(null)
    try {
      const data = await generateTitles({
        ...form,
        topic: form.topic.trim(),
        creator_profile: form.creator_profile.trim(),
        hook_types: form.hook_types.length > 0 ? form.hook_types : undefined,
      })
      setResults(data)
      toast.success(`生成了 ${data.titles.length} 个标题方案！`)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleHookType = (type) => {
    setForm(prev => ({
      ...prev,
      hook_types: prev.hook_types.includes(type)
        ? prev.hook_types.filter(t => t !== type)
        : [...prev.hook_types, type],
    }))
  }

  return (
    <div className="space-y-6">
      {/* 输入表单 */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
        {/* 选题输入 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            选题 / 主题 <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={form.topic}
            onChange={(e) => setForm(prev => ({ ...prev, topic: e.target.value }))}
            placeholder="例如：AI 科研工具推荐、考研复习攻略、职场穿搭..."
            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all text-gray-800 placeholder:text-gray-400"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* 平台选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select
              value={form.platform}
              onChange={(e) => setForm(prev => ({ ...prev, platform: e.target.value, hook_types: [] }))}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all bg-white text-gray-800"
            >
              {platforms.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* 生成数量 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">生成数量</label>
            <select
              value={form.count}
              onChange={(e) => setForm(prev => ({ ...prev, count: Number(e.target.value) }))}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all bg-white text-gray-800"
            >
              {[3, 5, 8, 10].map(n => (
                <option key={n} value={n}>{n} 个</option>
              ))}
            </select>
          </div>
        </div>

        {/* 创作者画像 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            创作者画像 <span className="text-gray-400 font-normal">（可选）</span>
          </label>
          <input
            type="text"
            value={form.creator_profile}
            onChange={(e) => setForm(prev => ({ ...prev, creator_profile: e.target.value }))}
            placeholder="例如：AI 科研账号、美妆博主、健身教练..."
            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none transition-all text-gray-800 placeholder:text-gray-400"
          />
        </div>

        {/* 钩子类型 */}
        {hookTypes.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              钩子类型 <span className="text-gray-400 font-normal">（可选，不选则自动匹配）</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {hookTypes.map(type => (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleHookType(type)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm transition-all duration-200
                    ${form.hook_types.includes(type)
                      ? 'bg-primary-100 text-primary-700 border border-primary-300 shadow-sm'
                      : 'bg-gray-50 text-gray-500 border border-gray-200 hover:bg-gray-100'
                    }
                  `}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 提交按钮 */}
        <button
          type="submit"
          disabled={loading}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-gradient-to-r from-primary-600 to-purple-600 text-white font-medium shadow-lg shadow-primary-200 hover:shadow-xl hover:from-primary-700 hover:to-purple-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              AI 正在生成中...
            </>
          ) : (
            <>
              <HiOutlineRocketLaunch className="w-5 h-5" />
              生成爆款标题
            </>
          )}
        </button>
      </form>

      {/* 加载状态 */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Array.from({ length: form.count }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl p-5 border border-gray-100">
              <div className="shimmer h-6 w-3/4 rounded-lg mb-3" />
              <div className="shimmer h-4 w-1/2 rounded-lg mb-2" />
              <div className="shimmer h-3 w-full rounded-lg" />
            </div>
          ))}
        </div>
      )}

      {/* 结果展示 */}
      {results && !loading && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <HiOutlineSparkles className="w-5 h-5 text-primary-500" />
            <h3 className="font-semibold text-gray-800">
              为「{results.topic}」生成了 {results.titles.length} 个标题方案
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {results.titles.map((title, idx) => (
              <TitleCard key={idx} title={title} index={idx} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
