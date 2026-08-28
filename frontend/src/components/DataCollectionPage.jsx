import { useEffect, useMemo, useState } from 'react';
import {
  askDataCollection,
  createCollectionJob,
  getCollectedContents,
  getCollectionJobs,
  getDataCollectionOverview,
  getDataQualityReport,
  manualCollect,
  runCollectionJob,
} from '../api/client';

const PLATFORMS = [
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'bilibili', label: 'B站' },
  { value: 'weibo', label: '微博' },
];

const SOURCE_TYPES = [
  { value: 'hot_search', label: '热榜趋势' },
  { value: 'keyword_content', label: '关键词内容' },
  { value: 'competitor_content', label: '竞品内容' },
];

function inferKeywordQuestion(text) {
  const value = (text || '').trim();
  const platform = PLATFORMS.find((p) => value.includes(p.label))?.value || 'douyin';
  const match = value.match(/(?:找|搜索|获取|关于)\s*([\w\u4e00-\u9fa5\-_.]{2,30}?)(?:的|在|相关|内容|东西|视频|笔记|作品|信息)/);
  const keyword = match?.[1]?.replace(/抖音|小红书|微博|B站|哔哩哔哩|douyin|xiaohongshu|weibo|bilibili/gi, '').trim();
  if (!keyword) return null;
  return { platform, keyword };
}

function Metric({ label, value, tone = 'brand' }) {
  const toneMap = {
    brand: 'text-brand-300 bg-brand-500/10 border-brand-500/20',
    blue: 'text-blue-300 bg-blue-500/10 border-blue-500/20',
    amber: 'text-amber-300 bg-amber-500/10 border-amber-500/20',
    rose: 'text-rose-300 bg-rose-500/10 border-rose-500/20',
  };
  return (
    <div className={`rounded-lg border p-4 ${toneMap[tone]}`}>
      <p className="text-xs text-txt-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-txt-bright">{value}</p>
    </div>
  );
}

export default function DataCollectionPage() {
  const [overview, setOverview] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [contents, setContents] = useState([]);
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState('');
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [smartResult, setSmartResult] = useState(null);
  const [askError, setAskError] = useState('');
  const [form, setForm] = useState({
    name: '抖音热榜每日采集',
    platform: 'douyin',
    source_type: 'hot_search',
    keyword: '',
    account_id: '',
    account_name: '',
    limit: 20,
    schedule: 'manual',
    purpose: 'trend_analysis',
  });

  const needsAccount = form.source_type === 'competitor_content';

  const loadAll = async () => {
    setLoading(true);
    try {
      const [ov, jobRes, contentRes, qualityRes] = await Promise.all([
        getDataCollectionOverview(7),
        getCollectionJobs({ size: 10 }),
        getCollectedContents({ size: 12 }),
        getDataQualityReport(),
      ]);
      setOverview(ov.data);
      setJobs(jobRes.data.items || []);
      setContents(contentRes.data.items || []);
      setQuality(qualityRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const createJob = async () => {
    const body = {
      name: form.name,
      schedule: form.schedule,
      purpose: form.purpose,
      status: 'active',
      target: {
        platform: form.platform,
        source_type: form.source_type,
        keyword: form.keyword,
        account_id: form.account_id,
        account_name: form.account_name,
        limit: Number(form.limit) || 20,
      },
    };
    await createCollectionJob(body);
    await loadAll();
  };

  const collectNow = async () => {
    setRunning('manual');
    try {
      await manualCollect({
        platform: form.platform,
        source_type: form.source_type,
        keyword: form.keyword,
        account_id: form.account_id,
        account_name: form.account_name,
        limit: Number(form.limit) || 20,
      });
      await loadAll();
    } finally {
      setRunning('');
    }
  };

  const askAndCollect = async () => {
    const text = question.trim();
    if (!text || asking) return;
    const inferred = inferKeywordQuestion(text);
    if (inferred) {
      setForm((prev) => ({
        ...prev,
        name: `${inferred.keyword} ${PLATFORMS.find((p) => p.value === inferred.platform)?.label || inferred.platform}内容采集`,
        platform: inferred.platform,
        source_type: 'keyword_content',
        keyword: inferred.keyword,
      }));
    }
    setAsking(true);
    setSmartResult(null);
    setAskError('');
    try {
      const result = await askDataCollection(text);
      setSmartResult(result.data);
      await loadAll();
    } catch (err) {
      setAskError(err?.response?.data?.detail || err?.message || '智能采集失败');
    } finally {
      setAsking(false);
    }
  };

  const runJob = async (id) => {
    setRunning(id);
    try {
      await runCollectionJob(id);
      await loadAll();
    } finally {
      setRunning('');
    }
  };

  const qualityTone = useMemo(() => {
    const score = overview?.avg_quality || 0;
    if (score >= 0.85) return 'brand';
    if (score >= 0.7) return 'amber';
    return 'rose';
  }, [overview]);

  return (
    <div className="min-h-screen p-6 space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-txt-bright">市场与竞品</h2>
          <p className="text-sm text-txt-secondary mt-1">围绕品牌词、商品词和竞品账号采集内容样本，判断选题和卖点机会</p>
        </div>
        <button className="btn-secondary w-fit" onClick={loadAll} disabled={loading}>
          {loading ? '刷新中...' : '刷新数据'}
        </button>
      </div>

      <section className="card p-5 space-y-4 border-brand-500/20">
        <div>
          <h3 className="text-base font-semibold text-txt-bright">一句话找市场信息</h3>
          <p className="text-xs text-txt-muted mt-1">输入品牌、商品或竞品需求，系统自动判断平台和数据源，先采集再分析</p>
        </div>
        <div className="flex flex-col lg:flex-row gap-3">
          <input
            className="input flex-1"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setSmartResult(null);
              setAskError('');
            }}
            onKeyDown={(e) => { if (e.key === 'Enter') askAndCollect(); }}
            placeholder="例如：找珀莱雅在抖音相关内容；小红书有哪些双抗水乳爆款笔记？"
          />
          <button className="btn-primary lg:w-36" onClick={askAndCollect} disabled={asking || !question.trim()}>
            {asking ? '采集中...' : '自动获取'}
          </button>
        </div>
        {askError && (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
            {askError}
          </div>
        )}

        {smartResult && (
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">
            <div className="rounded-lg border border-panel-border bg-panel-100/40 p-4">
              <p className="text-sm font-semibold text-txt-bright mb-2">分析结果</p>
              <p className="text-sm text-txt-secondary whitespace-pre-wrap leading-relaxed">{smartResult.answer}</p>
            </div>
            <div className="rounded-lg border border-panel-border bg-panel-100/40 p-4 space-y-3">
              <div>
                <p className="text-xs text-txt-muted">自动计划</p>
                <p className="text-sm text-txt-primary mt-1">
                  {smartResult.plan?.platform} / {smartResult.plan?.source_type}
                </p>
                <p className="text-xs text-txt-muted mt-1">
                  关键词：{smartResult.plan?.keyword || smartResult.plan?.account_name || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-txt-muted">采集诊断</p>
                <p className="text-sm text-txt-primary mt-1">
                  {smartResult.collection?.source_status || '-'}
                  {smartResult.collection?.fallback_used ? ' / 已使用兜底源' : ''}
                </p>
                {smartResult.collection?.failure_reason && (
                  <p className="text-xs text-rose-300 mt-1">{smartResult.collection.failure_reason}</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Metric label="记录条数" value={smartResult.collection?.items_recorded ?? 0} />
                <Metric label="质量分" value={smartResult.collection?.avg_quality ?? 0} tone="blue" />
              </div>
              <div>
                <p className="text-xs text-txt-muted mb-2">采集证据</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {(smartResult.evidence || []).slice(0, 5).map((item, idx) => (
                    <div key={`${item.entity_id || item.title}-${idx}`} className="text-xs text-txt-secondary rounded-md bg-panel-50/70 border border-panel-border px-2 py-1.5">
                      {item.url ? (
                        <a className="block truncate text-txt-primary hover:text-brand-300" href={item.url} target="_blank" rel="noreferrer">
                          {item.title || item.entity_id || '-'}
                        </a>
                      ) : (
                        <p className="truncate text-txt-primary">{item.title || item.entity_id || '-'}</p>
                      )}
                      <p className="mt-0.5">热度/播放：{item.metrics?.heat_score || item.metrics?.views || 0}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Metric label="采集任务" value={overview?.total_jobs ?? '-'} />
        <Metric label="活跃任务" value={overview?.active_jobs ?? '-'} tone="blue" />
        <Metric label="7日原始事件" value={overview?.raw_events ?? '-'} tone="amber" />
        <Metric label="标准内容" value={overview?.standard_contents ?? '-'} />
        <Metric label="平均质量" value={overview?.avg_quality ?? '-'} tone={qualityTone} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[420px_1fr] gap-5">
        <section className="card p-5 space-y-4">
          <div>
            <h3 className="text-base font-semibold text-txt-bright">创建采集任务</h3>
            <p className="text-xs text-txt-muted mt-1">任务可保存，也可以立即执行一次</p>
          </div>

          <div className="space-y-3">
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="任务名称" />
            <div className="grid grid-cols-2 gap-3">
              <select className="select" value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })}>
                {PLATFORMS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
              <select className="select" value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
                {SOURCE_TYPES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            {needsAccount ? (
              <div className="grid grid-cols-2 gap-3">
                <input className="input" value={form.account_name} onChange={(e) => setForm({ ...form, account_name: e.target.value })} placeholder="竞品账号名" />
                <input className="input" value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value })} placeholder="账号 ID/UID" />
              </div>
            ) : (
              <input
                className="input"
                value={form.keyword}
                onChange={(e) => setForm({ ...form, keyword: e.target.value })}
                placeholder={form.source_type === 'keyword_content' ? '关键词，例如：珀莱雅' : '关键词，可留空'}
              />
            )}
            <div className="grid grid-cols-2 gap-3">
              <select className="select" value={form.schedule} onChange={(e) => setForm({ ...form, schedule: e.target.value })}>
                <option value="manual">手动</option>
                <option value="hourly">每小时</option>
                <option value="daily">每日</option>
                <option value="weekly">每周</option>
              </select>
              <input className="input" type="number" min="1" max="100" value={form.limit} onChange={(e) => setForm({ ...form, limit: e.target.value })} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button className="btn-secondary" onClick={createJob}>保存任务</button>
            <button className="btn-primary" onClick={collectNow} disabled={running === 'manual'}>
              {running === 'manual' ? '采集中...' : '立即采集'}
            </button>
          </div>
        </section>

        <section className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-txt-bright">采集任务</h3>
            <span className="text-xs text-txt-muted">{jobs.length} 个最近任务</span>
          </div>
          <div className="space-y-2">
            {jobs.length === 0 && <p className="text-sm text-txt-muted py-8 text-center">暂无采集任务</p>}
            {jobs.map((job) => (
              <div key={job.id} className="rounded-lg border border-panel-border bg-panel-100/40 p-3 flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-txt-bright truncate">{job.name}</p>
                  <p className="text-xs text-txt-muted mt-1">
                    {job.target?.platform} / {job.target?.source_type} / {job.schedule} / {job.last_status || 'never_run'}
                  </p>
                </div>
                <button className="btn-secondary px-3 py-1.5 text-xs" onClick={() => runJob(job.id)} disabled={running === job.id}>
                  {running === job.id ? '运行中' : '运行'}
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
        <section className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-txt-bright">最新标准内容</h3>
            <span className="text-xs text-txt-muted">{contents.length} 条</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-txt-muted border-b border-panel-border">
                <tr>
                  <th className="text-left py-2 font-medium">标题</th>
                  <th className="text-left py-2 font-medium">平台</th>
                  <th className="text-right py-2 font-medium">播放</th>
                  <th className="text-right py-2 font-medium">点赞</th>
                  <th className="text-right py-2 font-medium">质量</th>
                </tr>
              </thead>
              <tbody>
                {contents.map((item) => (
                  <tr key={item.id} className="border-b border-panel-border/60">
                    <td className="py-3 pr-4 text-txt-primary max-w-[520px] truncate">{item.title || item.entity_id || '-'}</td>
                    <td className="py-3 text-txt-secondary">{item.platform}</td>
                    <td className="py-3 text-right text-txt-secondary">{item.metrics?.views || item.metrics?.heat_score || 0}</td>
                    <td className="py-3 text-right text-txt-secondary">{item.metrics?.likes || 0}</td>
                    <td className="py-3 text-right text-brand-300">{item.quality?.score ?? '-'}</td>
                  </tr>
                ))}
                {contents.length === 0 && (
                  <tr><td colSpan="5" className="py-10 text-center text-txt-muted">暂无标准化内容</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card p-5">
          <h3 className="text-base font-semibold text-txt-bright mb-4">数据质量</h3>
          <div className="space-y-3">
            <Metric label="抽样数量" value={quality?.sample_size ?? '-'} tone="blue" />
            <Metric label="低质量记录" value={quality?.low_quality_count ?? '-'} tone="amber" />
            <Metric label="重复记录" value={quality?.duplicate_count ?? '-'} tone="rose" />
          </div>
          <div className="mt-4 space-y-2">
            {(quality?.issues || []).slice(0, 4).map((issue) => (
              <div key={issue.id} className="rounded-lg bg-panel-100/40 border border-panel-border p-3">
                <p className="text-xs text-txt-primary truncate">{issue.platform} / {issue.source_type}</p>
                <p className="text-xs text-txt-muted mt-1">质量分 {issue.quality?.score}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
