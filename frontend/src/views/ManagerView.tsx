import { KpiCard } from '@/components/ui/KpiCard';
import { IntegrationStatus } from '@/components/ui/IntegrationStatus';
import { 
  kpiData, 
  incidentsBySource, 
  volumeTrend, 
  topCategories, 
  priorityByTeam,
  integrationHealth 
} from '@/data/mockData';
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

export function ManagerView() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-foreground">AI-Powered Support — Executive Overview</h1>
        <p className="text-muted-foreground mt-1">Real-time incident intelligence and system health</p>
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-5 gap-4">
        <KpiCard 
          title="Open Tickets" 
          value={kpiData.openTickets}
          trend={kpiData.openTicketsTrend}
          trendLabel="vs yesterday"
          status={kpiData.openTickets > 50 ? 'warning' : 'success'}
        />
        <KpiCard 
          title="SLA Breaches (24h)" 
          value={kpiData.slaBreaches}
          trend={kpiData.slaBreachesTrend}
          trendLabel="breaches"
          status={kpiData.slaBreaches > 5 ? 'error' : kpiData.slaBreaches > 0 ? 'warning' : 'success'}
        />
        <KpiCard 
          title="Avg Time to Assignment" 
          value={kpiData.avgTimeToAssignment}
          trend={kpiData.assignmentTrend}
          trendLabel="time"
          status="success"
        />
        <KpiCard 
          title="MTTR" 
          value={kpiData.mttr}
          trend={kpiData.mttrTrend}
          trendLabel="time"
          status="success"
        />
        <KpiCard 
          title="Suggestions Accepted" 
          value={`${kpiData.suggestionsAccepted}%`}
          trend={kpiData.acceptedTrend}
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

        {/* Top Categories */}
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
                width={100}
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
        {/* Priority by Team Heatmap */}
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

        {/* Integration Health */}
        <div className="kpi-card">
          <h3 className="mb-4">Integration Health</h3>
          <div className="space-y-1">
            {integrationHealth.map((integration) => (
              <IntegrationStatus
                key={integration.name}
                name={integration.name}
                status={integration.status as 'healthy' | 'warning' | 'error'}
                lastSync={integration.lastSync}
              />
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-4 pt-3 border-t border-border">
            Data Residency: All processing & storage in India (region: ap-south-1)
          </p>
        </div>
      </div>
    </div>
  );
}
