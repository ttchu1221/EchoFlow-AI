import { useState } from 'react'
import toast from 'react-hot-toast'
import { HiOutlineClipboardDocument, HiOutlineCheck, HiOutlineBolt, HiOutlineFaceSmile, HiOutlineLightBulb } from 'react-icons/hi2'

export default function TitleCard({ title, index }) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(title.title)
    setCopied(true)
    toast.success('已复制到剪贴板')
    setTimeout(() => setCopied(false), 2000)
  }

  const scoreColor = (title.predicted_heat || 0) >= 7
    ? 'text-green-600 bg-green-50'
    : (title.predicted_heat || 0) >= 5
    ? 'text-yellow-600 bg-yellow-50'
    : 'text-gray-600 bg-gray-50'

  return (
    <div className="group bg-white rounded-xl border border-gray-100 p-5 card-hover relative overflow-hidden">
      {/* 序号装饰 */}
      <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-gradient-to-br from-primary-100 to-purple-100 flex items-center justify-center">
        <span className="text-xs font-bold text-primary-600">{index + 1}</span>
      </div>

      {/* 标题 */}
      <h4 className="text-base font-semibold text-gray-800 pr-10 mb-3 leading-relaxed">
        {title.title}
      </h4>

      {/* 标签行 */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-primary-50 text-primary-700 text-xs font-medium">
          <HiOutlineBolt className="w-3 h-3" />
          {title.hook_type}
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-accent-50 text-accent-700 text-xs font-medium">
          <HiOutlineFaceSmile className="w-3 h-3" />
          {title.emotion}
        </span>
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${scoreColor}`}>
          热度 {(title.predicted_heat || 0).toFixed(1)}
        </span>
      </div>

      {/* 解释 */}
      <p className="text-xs text-gray-500 leading-relaxed mb-3 flex items-start gap-1.5">
        <HiOutlineLightBulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-400" />
        {title.reason || title.explanation}
      </p>

      {/* 复制按钮 */}
      <button
        onClick={copyToClipboard}
        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-primary-600 transition-colors"
      >
        {copied ? (
          <>
            <HiOutlineCheck className="w-3.5 h-3.5" />
            已复制
          </>
        ) : (
          <>
            <HiOutlineClipboardDocument className="w-3.5 h-3.5" />
            复制标题
          </>
        )}
      </button>
    </div>
  )
}
