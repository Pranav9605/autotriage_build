import { useState, useEffect } from 'react';
import { KpiCard } from '@/components/ui/KpiCard';
import { IntegrationStatus } from '@/components/ui/IntegrationStatus';
import { incidentsBySource, volumeTrend, priorityByTeam } from '@/data/mockData';
import { api, DashboardKPIs, ModuleAccuracy, HealthStatus } from '@/services/api';
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

function formatMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatMttr(hours: number | null): string {
  if (hours === null) return 'N/A';
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  return `${hours.toFixed(1)}h`;
}

type IntegrationEntry = { name: string; status: 'healthy' | 'warning' | 'error'; lastSync: string };

function healthComponentsToIntegrations(components: Record<string, string>): IntegrationEntry[] {
  return Object.entries(components).map(([name, status]) => ({
    name,
    status: status === 'ok' ? 'healthy' : status === 'degraded' ? 'warning' : 'error',
    lastSync: 'just now',
  }));
}

export function ManagerView() {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [moduleAccuracy, setModuleAccuracy] = useState<ModuleAccuracy[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [kpiData, modData, healthData] = await Promise.all([
          api.getDashboardKPIs(),
          api.getModuleAccuracy(),
          api.getHealth(),
        ]);
        if (!cancelled) {
          setKpis(kpiData);
          setModuleAccuracy(modData);
          setHealth(healthData);
        }
      } catch {
        // backend offline — keep null, UI shows mock fallback values
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const openTickets = kpis ? kpis.total_tickets - kpis.triaged_tickets : 23;
  const slaBreaches = kpis ? kpis.manual_review_count : 2;
  const avgLatency = kpis ? formatMs(kpis.avg_latency_ms) : '4.2s';
  const mttr = kpis ? formatMttr(kpis.mttr_hours) : '3.8h';
  const acceptedPct = kpis ? Math.round(kpis.accuracy_rate * 100) : 81;

  const topCategories = moduleAccuracy.length > 0
    ? moduleAccuracy.map(m => ({ category: m.module, count: m.total }))
    : [
        { category: 'FI', count: 30 },
        { category: 'BASIS', count: 20 },
        { category: 'MM', count: 15 },
        { category: 'SD', count: 15 },
        { category: 'PI_PO', count: 10 },
        { category: 'ABAP', count: 10 },
      ];

  const integrationHealth: IntegrationEntry[] =
    health
      ? healthComponentsToIntegrations(health.components)
      : [
          { name: 'WhatsApp', status: 'healthy', lastSync: '2 min ago' },
          { name: 'Jira', status: 'healthy', lastSync: '1 min ago' },
          { name: 'SAP SolMan', status: 'warning', lastSync: '15 min ago' },
          { name: 'SAP CPI', status: 'healthy', lastSync: '30 sec ago' },
        ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground">AI-Powered Support — Executive Overview</h1>
          <p className="text-muted-foreground mt-1">Real-time incident intelligence and system health</p>
        </div>
        {loading && (
          <span className="text-xs text-muted-foreground animate-pulse">Loading live data…</span>
        )}
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-5 gap-4">
        <KpiCard
          title="Open Tickets"
          value={openTickets}
          trend={3}
          trendLabel="vs yesterday"
          status={openTickets > 50 ? 'warning' : 'success'}
        />
        <KpiCard
          title="Manual Reviews (24h)"
          value={slaBreaches}
          trend={-1}
          trendLabel="reviews"
          status={slaBreaches > 5 ? 'error' : slaBreaches > 0 ? 'warning' : 'success'}
        />
        <KpiCard
          title="Avg Triage Latency"
          value={avgLatency}
          trend={-8}
          trendLabel="time"
          status="success"
        />
        <KpiCard
          title="MTTR"
          value={mttr}
          trend={-15}
          trendLabel="time"
          status="success"
        />
        <KpiCard
          title="Suggestions Accepted"
          value={`${acceptedPct}%`}
          trend={5}
          trendLabel="vs last week"
          status="success"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-6">
        {/* Incidents by Source */}
        <div className="kpi-card">
          <h3 className="mb-4">Incidents by Source</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={incidentsBySource}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {incidentsBySource.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Volume Trend */}
        <div className="kpi-card">
          <h3 className="mb-4">Volume Trend (7 days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={volumeTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
              />
              <Line
                type="monotone"
                dataKey="incidents"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ fill: 'hsl(var(--primary))', strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Categories — live from backend */}
        <div className="kpi-card">
          <h3 className="mb-4">Top Categories</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={topCategories} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis type="number" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis
                dataKey="category"
                type="category"
                tick={{ fontSize: 11 }}
                stroke="hsl(var(--muted-foreground))"
                width={60}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Priority by Team */}
        <div className="kpi-card">
          <h3 className="mb-4">Priority Distribution by Team</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={priorityByTeam}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="team" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Bar dataKey="P1" stackId="a" fill="hsl(var(--priority-p1))" />
              <Bar dataKey="P2" stackId="a" fill="hsl(var(--priority-p2))" />
              <Bar dataKey="P3" stackId="a" fill="hsl(var(--priority-p3))" />
              <Bar dataKey="P4" stackId="a" fill="hsl(var(--priority-p4))" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Integration Health — live from backend */}
        <div className="kpi-card">
          <h3 className="mb-4">Integration Health</h3>
          <div className="space-y-1">
            {integrationHealth.map((integration) => (
              <IntegrationStatus
                key={integration.name}
                name={integration.name}
                status={integration.status}
                lastSync={integration.lastSync}
              />
            ))}
          </div>
          {kpis && (
            <div className="mt-4 pt-3 border-t border-border grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-xs text-muted-foreground">Total Triaged</p>
                <p className="text-sm font-semibold">{kpis.triaged_tickets}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Avg Confidence</p>
                <p className="text-sm font-semibold">{Math.round(kpis.avg_confidence * 100)}%</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Override Rate</p>
                <p className="text-sm font-semibold">{Math.round(kpis.override_rate * 100)}%</p>
              </div>
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-3 pt-3 border-t border-border">
            Data Residency: All processing & storage in India (region: ap-south-1)
          </p>
        </div>
      </div>
    </div>
  );
}
