import { useState } from 'react';
import { runFullPipeline } from '../api/client';
import { withLLMProvider } from '../utils/llmProvider';

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'douyin', name: '抖音' },
  { id: 'bilibili', name: 'B站' },
  { id: 'youtube_shorts', name: 'YouTube Shorts' },
  { id: 'weibo', name: '微博' },
];

const STEPS = [
  { id: 'titles',   label: '标题生成', icon: '✍️' },
  { id: 'trends',   label: '趋势分析', icon: '📊' },
  { id: 'script',   label: '脚本生成', icon: '📝' },
  { id: 'cover',    label: '封面设计', icon: '🎨' },
  { id: 'publish',  label: '发布策略', icon: '📡' },
];

export default function PipelinePanel() {
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState('titles');

  const handleRun = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const data = await runFullPipeline(withLLMProvider({ topic, platform }));
      setResult(data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">全流程智能体</h2>
        <p className="text-sm text-gray-500 mt-1">一键执行完整的 AI 内容生产流水线</p>
      </div>

      <div className="card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">内容主题</label>
            <input
              type="text"
              className="input"
              placeholder="输入你的内容主题..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRun()}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">目标平台</label>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <button className="btn-primary w-full" onClick={handleRun} disabled={loading || !topic.trim()}>
          {loading ? <><span className="animate-spin">⏳</span> 全流程执行中，请稍候...</> : '🚀 启动全流程'}
        </button>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          {/* 步骤导航 */}
          <div className="card p-2 flex gap-1 overflow-x-auto">
            {STEPS.map((step) => (
              <button
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                className={`
                  flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all
                  ${activeStep === step.id
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-gray-500 hover:bg-gray-50'
                  }
                `}
              >
                <span>{step.icon}</span>
                {step.label}
                {result[step.id] && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
              </button>
            ))}
          </div>

          {/* 标题结果 */}
          {activeStep === 'titles' && result.titles && (
            <div className="space-y-3">
              {result.titles.map((item, i) => (
                <div key={i} className="card p-5">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h4 className="font-semibold text-gray-900 flex-1">{item.title}</h4>
                    <span className="tag-blue">热度 {item.predicted_heat}</span>
                  </div>
                  <p className="text-sm text-gray-500">{item.reason}</p>
                </div>
              ))}
            </div>
          )}

          {/* 趋势结果 */}
          {activeStep === 'trends' && result.trends && (
            <div className="space-y-3">
              {result.trends.trending_topics?.map((t, i) => (
                <div key={i} className="card p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-gray-900">{t.topic}</h4>
                    <span className="tag-blue">热度 {t.heat_score}</span>
                  </div>
                  <p className="text-sm text-gray-500">{t.reason}</p>
                </div>
              ))}
            </div>
          )}

          {/* 脚本结果 */}
          {activeStep === 'script' && result.script && (
            <div className="card p-6">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-sans">{result.script.full_script}</pre>
            </div>
          )}

          {/* 封面结果 */}
          {activeStep === 'cover' && result.cover && (
            <div className="space-y-3">
              {result.cover.cover_texts?.map((ct, i) => (
                <div key={i} className="card p-6">
                  <div className="rounded-2xl p-8 mb-4 text-center min-h-[160px] flex flex-col items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500">
                    <h3 className="text-2xl font-bold text-white drop-shadow-lg">{ct.main_text}</h3>
                    {ct.sub_text && <p className="text-white/80 mt-2">{ct.sub_text}</p>}
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="text-gray-400">字体：</span>{ct.font_style}</div>
                    <div><span className="text-gray-400">背景：</span>{ct.background_suggestion}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 发布结果 */}
          {activeStep === 'publish' && result.publish && (
            <div className="space-y-3">
              {result.publish.publish_time && (
                <div className="card p-5">
                  <h4 className="font-semibold text-gray-800 mb-2">⏰ {result.publish.publish_time.best_time}</h4>
                  <p className="text-sm text-gray-500">{result.publish.publish_time.reason}</p>
                </div>
              )}
              {result.publish.hashtags?.length > 0 && (
                <div className="card p-5">
                  <div className="flex flex-wrap gap-2">
                    {result.publish.hashtags.map((tag, i) => (
                      <span key={i} className="tag-blue">#{tag}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
