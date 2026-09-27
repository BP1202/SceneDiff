import React, { useState } from 'react'
import {
  Terminal,
  Database,
  ShieldCheck,
  AlertTriangle,
  Info,
  Key,
} from 'lucide-react'
import { useComparisonStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Tabs } from '../../components/ui/Tabs'
import { Badge } from '../../components/ui/Badge'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './ConsoleStorageViewer.css'

export const ConsoleStorageViewer: React.FC = () => {
  const { summary } = useComparisonStore()
  const [activeTab, setActiveTab] = useState('console')

  const tabs = [
    {
      id: 'console',
      label: 'Browser Console & Errors',
      icon: <Terminal size={14} />,
      count: summary.consoleDiffs.length,
      severity: 'HIGH' as const,
    },
    {
      id: 'storage',
      label: 'Storage & Cookies (Masked)',
      icon: <Database size={14} />,
      count: summary.storageDiffs.length,
    },
  ]

  return (
    <div className="sd-console-storage animate-fade-in">
      <SectionHeader
        title="Runtime Console & Storage Comparator"
        subtitle="Uncaught browser runtime exceptions and web storage alterations captured during trace replay under Secret Shield protection."
        icon={<Terminal size={20} />}
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Console */}
      {activeTab === 'console' && (
        <div className="sd-console-tab animate-fade-in">
          <Card>
            <CardHeader>
              <CardTitle>
                <Terminal size={16} /> Uncaught JavaScript Exceptions & Warnings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="sd-console-list">
                {summary.consoleDiffs.map((item) => (
                  <div key={item.id} className={`sd-console-item is-${item.type}`}>
                    <div className="sd-console-item__header">
                      <div className="sd-console-item__title-row">
                        {item.type === 'error' ? (
                          <AlertTriangle size={15} className="text-danger" />
                        ) : (
                          <Info size={15} className="text-warning" />
                        )}
                        <span className="sd-console-item__msg">{item.message}</span>
                      </div>
                      <Badge severity={item.severity} size="sm">
                        {item.occurrence.toUpperCase()}
                      </Badge>
                    </div>
                    {item.stackTrace && (
                      <pre className="sd-console-item__stack">
                        {item.stackTrace}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Storage */}
      {activeTab === 'storage' && (
        <div className="sd-storage-tab animate-fade-in">
          <Card>
            <CardHeader>
              <CardTitle>
                <Key size={16} /> Web Storage Differences (LocalStorage & SessionStorage)
              </CardTitle>
              <div className="sd-storage__shield-pill">
                <ShieldCheck size={13} /> Secret Shield Auto-Redacted
              </div>
            </CardHeader>
            <CardContent>
              <table className="sd-storage-table">
                <thead>
                  <tr>
                    <th>Storage Type</th>
                    <th>Key Identifier</th>
                    <th>Commit A (Base Value)</th>
                    <th>Commit B (Head Value)</th>
                    <th>Secret Status</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.storageDiffs.map((item) => (
                    <tr key={item.key}>
                      <td>
                        <span className="sd-storage-type font-mono">{item.storageType}</span>
                      </td>
                      <td>
                        <code className="sd-storage-key">{item.key}</code>
                      </td>
                      <td>
                        <span className="sd-storage-val">{item.baseValue || '(none)'}</span>
                      </td>
                      <td>
                        <span className="sd-storage-val is-head">{item.headValue || '(none)'}</span>
                      </td>
                      <td>
                        {item.isSecretMasked ? (
                          <span className="sd-shield-masked-badge">
                            <ShieldCheck size={11} /> MASKED
                          </span>
                        ) : (
                          <span className="sd-plain-badge">Plaintext</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
