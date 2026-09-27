import React from 'react'
import {
  Gauge,
  Clock,
  Cpu,
  Zap,
} from 'lucide-react'
import { useComparisonStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { MetricCard } from '../../components/ui/MetricCard'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './PerformanceDashboard.css'

export const PerformanceDashboard: React.FC = () => {
  const { summary } = useComparisonStore()

  const ttfb = summary.performanceDiffs.find((p) => p.metric === 'TTFB')
  const lcp = summary.performanceDiffs.find((p) => p.metric === 'LCP')
  const fcp = summary.performanceDiffs.find((p) => p.metric === 'FCP')
  const heap = summary.performanceDiffs.find((p) => p.metric === 'JS_Heap')

  return (
    <div className="sd-performance-dashboard animate-fade-in">
      <SectionHeader
        title="Web Performance & Latency Regressions"
        subtitle="Measures Core Web Vitals and resource footprint regressions between Commit A and Commit B."
        icon={<Gauge size={20} />}
      />

      {/* Top Vital Metric Cards */}
      <div className="sd-perf-cards-grid">
        <MetricCard
          title="TTFB (Time to First Byte)"
          value={`${ttfb?.headValue || 620}ms`}
          trend={{ value: `+${ttfb?.deltaPercent || 416}% slower`, isPositive: false }}
          subtext="Base: 120ms (Regression)"
          icon={<Clock size={18} />}
          accentColor="critical"
        />
        <MetricCard
          title="LCP (Largest Contentful Paint)"
          value={`${lcp?.headValue || 1420}ms`}
          trend={{ value: `+${lcp?.deltaPercent || 121}% delay`, isPositive: false }}
          subtext="Base: 640ms"
          icon={<Zap size={18} />}
          accentColor="warning"
        />
        <MetricCard
          title="FCP (First Contentful Paint)"
          value={`${fcp?.headValue || 380}ms`}
          trend={{ value: `+${fcp?.deltaPercent || 22}%`, isPositive: true }}
          subtext="Base: 310ms (Acceptable)"
          icon={<Gauge size={18} />}
          accentColor="primary"
        />
        <MetricCard
          title="JS Heap Allocation"
          value={`${heap?.headValue || 26.2}MB`}
          trend={{ value: `+${heap?.deltaPercent || 6.9}%`, isPositive: true }}
          subtext="Base: 24.5MB (Normal)"
          icon={<Cpu size={18} />}
          accentColor="success"
        />
      </div>

      {/* Detailed Comparative Bar Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Gauge size={16} /> Comparative Web Vitals Delta
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="sd-perf-bars-list">
            {summary.performanceDiffs.map((item) => {
              const maxVal = Math.max(item.baseValue, item.headValue) * 1.2
              const baseWidth = Math.min(100, (item.baseValue / maxVal) * 100)
              const headWidth = Math.min(100, (item.headValue / maxVal) * 100)
              const isDegraded = item.deltaPercent > 30

              return (
                <div key={item.metric} className="sd-perf-bar-row">
                  <div className="sd-perf-bar-meta">
                    <span className="sd-perf-metric-name">{item.metric}</span>
                    <div className="sd-perf-metric-values">
                      <span className="val-base">Base A: {item.baseValue}{item.unit}</span>
                      <span className="divider">vs</span>
                      <span className={`val-head ${isDegraded ? 'text-critical' : ''}`}>
                        Head B: {item.headValue}{item.unit}
                      </span>
                      <Badge
                        severity={item.severity}
                        size="sm"
                      >
                        {item.deltaPercent > 0 ? `+${item.deltaPercent}%` : `${item.deltaPercent}%`}
                      </Badge>
                    </div>
                  </div>

                  <div className="sd-perf-bar-visual">
                    {/* Baseline Bar */}
                    <div className="sd-bar-track">
                      <div
                        className="sd-bar-fill is-base"
                        style={{ width: `${baseWidth}%` }}
                        title={`Baseline: ${item.baseValue}${item.unit}`}
                      />
                    </div>
                    {/* Head Bar */}
                    <div className="sd-bar-track">
                      <div
                        className={`sd-bar-fill ${isDegraded ? 'is-regressed' : 'is-normal'}`}
                        style={{ width: `${headWidth}%` }}
                        title={`Head: ${item.headValue}${item.unit}`}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
