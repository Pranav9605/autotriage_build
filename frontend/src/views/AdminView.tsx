import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
import { IntegrationStatus } from '@/components/ui/IntegrationStatus';
import { api, PipelineStats } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { 
  Plug, 
  Database, 
  Brain, 
  Shield, 
  Users,
  Upload,
  Download,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Cpu,
  BookOpen,
  Sparkles,
  HardDrive,
  Loader2
} from 'lucide-react';

export function AdminView() {
  const [confidenceThreshold, setConfidenceThreshold] = useState([80]);
  const [autoApply, setAutoApply] = useState(false);
  const [piiRedaction, setPiiRedaction] = useState(true);
  const [pipelineStats, setPipelineStats] = useState<PipelineStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [loadingIntegrations, setLoadingIntegrations] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  useEffect(() => {
    const fetchPipelineStats = async () => {
      setStatsLoading(true);
      setStatsError(null);
      try {
        const stats = await api.getPipelineStats();
        setPipelineStats(stats);
      } catch (err) {
        // Silently handle - show placeholder if backend unavailable
        console.warn('Pipeline stats fetch failed - backend may be offline');
      } finally {
        setStatsLoading(false);
      }
    };
    fetchPipelineStats();
  }, []);

  const integrations = [
    { name: 'WhatsApp Business', status: 'healthy' as const, lastSync: '2 min ago', details: '+91 98765 43210' },
    { name: 'Jira Cloud', status: 'healthy' as const, lastSync: '1 min ago', details: 'company.atlassian.net' },
    { name: 'SAP Solution Manager', status: 'warning' as const, lastSync: '15 min ago', details: 'solman.company.com' },
    { name: 'SAP Service Cloud (C4C)', status: 'healthy' as const, lastSync: '5 min ago', details: 'c4c.company.com' },
    { name: 'SAP Integration Suite (CPI)', status: 'healthy' as const, lastSync: '30 sec ago', details: 'cpi.company.com' },
  ];

  const categoryMappings = [
    { category: 'GL Posting', sapModule: 'FI', jiraComponent: 'Finance - GL' },
    { category: 'Workflow', sapModule: 'BC-BMT', jiraComponent: 'Platform - Workflow' },
    { category: 'Output Management', sapModule: 'SD', jiraComponent: 'Sales - Output' },
    { category: 'Performance', sapModule: 'BC-CCM', jiraComponent: 'Platform - Performance' },
    { category: 'EDI/IDoc', sapModule: 'BC-MID', jiraComponent: 'Integration - EDI' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-foreground">Admin / Integrations</h1>
        <p className="text-muted-foreground mt-1">Manage connectors, taxonomy, AI controls, and security settings</p>
      </div>

      {/* Integrations Panel */}
      <div className="kpi-card">
        <div className="flex items-center gap-2 mb-4">
          <Plug className="w-5 h-5 text-primary" />
          <h2>Integrations</h2>
        </div>
        
        <div className="grid grid-cols-2 gap-6">
          {integrations.map((integration) => (
            <div key={integration.name} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`status-dot ${
                  integration.status === 'healthy' ? 'status-dot-success' : 
                  integration.status === 'warning' ? 'status-dot-warning' : 'status-dot-error'
                }`} />
                <div>
                  <p className="text-sm font-medium">{integration.name}</p>
                  <p className="text-xs text-muted-foreground">{integration.details}</p>
                  <p className="text-xs text-muted-foreground">Last sync: {integration.lastSync}</p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                disabled={loadingIntegrations.has(integration.name)}
                onClick={() => {
                  setLoadingIntegrations(prev => new Set([...prev, integration.name]));
                  setTimeout(() => {
                    setLoadingIntegrations(prev => {
                      const next = new Set(prev);
                      next.delete(integration.name);
                      return next;
                    });
                  }, 1500);
                }}
              >
                <RefreshCw className={`w-4 h-4 ${loadingIntegrations.has(integration.name) ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Taxonomy & Mapping */}
      <div className="kpi-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-primary" />
            <h2>Taxonomy & Mapping</h2>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-1.5">
              <Upload className="w-4 h-4" />
              Import CSV
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Download className="w-4 h-4" />
              Export
            </Button>
          </div>
        </div>

        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Category</th>
                <th className="text-left px-4 py-2 font-medium">SAP Module</th>
                <th className="text-left px-4 py-2 font-medium">Jira Component</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {categoryMappings.map((mapping) => (
                <tr key={mapping.category} className="hover:bg-muted/50">
                  <td className="px-4 py-2">{mapping.category}</td>
                  <td className="px-4 py-2 font-mono text-xs">{mapping.sapModule}</td>
                  <td className="px-4 py-2">{mapping.jiraComponent}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Pipeline Health */}
      <div className="kpi-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary" />
            <h2>AI Pipeline Health</h2>
          </div>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => {
              setStatsLoading(true);
              api.getPipelineStats()
                .then(setPipelineStats)
                .catch(() => setStatsError('Failed to refresh'))
                .finally(() => setStatsLoading(false));
            }}
          >
            <RefreshCw className={`w-4 h-4 ${statsLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {statsError && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg mb-4">
            <AlertCircle className="w-4 h-4" />
            {statsError}
          </div>
        )}

        {statsLoading && !pipelineStats ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* XGBoost Classifier */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-medium">XGBoost Classifier</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="status-dot status-dot-warning" />
                <span className="text-xs text-amber-600 font-medium">
                  Training threshold not met
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">inactive — &lt; 500 samples</p>
            </div>

            {/* Knowledge Base */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-4 h-4 text-green-500" />
                <span className="text-sm font-medium">Knowledge Base</span>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Articles:</span>
                  <span className="font-medium">{pipelineStats?.knowledge_base.total_articles ?? 0}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Total Hits:</span>
                  <span className="font-medium">{pipelineStats?.knowledge_base.total_hits ?? 0}</span>
                </div>
              </div>
            </div>

            {/* Response Cache */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <HardDrive className="w-4 h-4 text-yellow-500" />
                <span className="text-sm font-medium">Response Cache</span>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Entries:</span>
                  <span className="font-medium">{pipelineStats?.response_cache.total_entries ?? 0}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Total Hits:</span>
                  <span className="font-medium">{pipelineStats?.response_cache.total_hits ?? 0}</span>
                </div>
              </div>
            </div>

            {/* Claude Sonnet */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-purple-500" />
                <span className="text-sm font-medium">Claude Sonnet (Anthropic)</span>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <div className={`status-dot ${pipelineStats?.gemini.available ? 'status-dot-success' : 'status-dot-error'}`} />
                <span className="text-xs text-muted-foreground">
                  {pipelineStats?.gemini.available ? 'Available' : 'Unavailable'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground truncate">
                {pipelineStats?.gemini.model || 'claude-3-5-sonnet-20241022'}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* AI Controls */}
        <div className="kpi-card">
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-5 h-5 text-primary" />
            <h2>AI Controls</h2>
          </div>

          <div className="space-y-4">
            <div>
              <Label className="text-sm">Confidence Threshold: {confidenceThreshold[0]}%</Label>
              <p className="text-xs text-muted-foreground mb-2">
                Suggestions below this threshold will be flagged for manual review
              </p>
              <Slider
                value={confidenceThreshold}
                onValueChange={setConfidenceThreshold}
                max={100}
                step={5}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div>
                <Label>Auto-apply above threshold</Label>
                <p className="text-xs text-muted-foreground">
                  Automatically apply suggestions with high confidence
                </p>
              </div>
              <Switch checked={autoApply} onCheckedChange={setAutoApply} />
            </div>

            <Separator />

            <div>
              <Label className="text-sm">OCR Provider</Label>
              <select className="w-full mt-1 px-3 py-2 border border-border rounded-md text-sm bg-background">
                <option>Google Cloud Vision</option>
                <option>AWS Textract</option>
                <option>On-premises (Tesseract)</option>
              </select>
            </div>

            <Separator />

            <Button 
              variant="outline" 
              size="sm" 
              className="w-full gap-1.5"
              onClick={() => {
                toast({
                  title: "Retraining check",
                  description: "47 samples collected. Minimum 500 required. Pipeline will activate automatically."
                });
              }}
            >
              <RefreshCw className="w-4 h-4" />
              Trigger Model Retrain
            </Button>
          </div>
        </div>

        {/* Security & Data Residency */}
        <div className="kpi-card">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-primary" />
            <h2>Security & Data Residency</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-success/10 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-success" />
                <span className="text-sm font-medium">India Region Active</span>
              </div>
              <span className="text-xs text-muted-foreground">ap-south-1</span>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div>
                <Label>PII Redaction</Label>
                <p className="text-xs text-muted-foreground">
                  Redact personal information before AI processing
                </p>
              </div>
              <Switch checked={piiRedaction} onCheckedChange={setPiiRedaction} />
            </div>

            {piiRedaction && (
              <div>
                <Label className="text-sm">Redaction Patterns (Regex)</Label>
                <Input 
                  className="mt-1 font-mono text-xs"
                  defaultValue="\b[A-Z]{5}[0-9]{4}[A-Z]\b|\b\d{12}\b"
                  placeholder="Enter regex patterns..."
                />
              </div>
            )}

            <Separator />

            <div>
              <Label className="text-sm">Data Retention</Label>
              <select className="w-full mt-1 px-3 py-2 border border-border rounded-md text-sm bg-background">
                <option>90 days</option>
                <option>180 days</option>
                <option>1 year</option>
                <option>Custom...</option>
              </select>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2 text-sm">
                <AlertCircle className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">
                  All data encrypted with AES-256 at rest
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Roles & Permissions */}
      <div className="kpi-card">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-primary" />
          <h2>Roles & Permissions</h2>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium mb-2">Support Agent</h4>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>• View & claim incidents</li>
              <li>• Accept AI suggestions</li>
              <li>• Add comments</li>
            </ul>
          </div>
          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium mb-2">Team Lead</h4>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>• All agent permissions</li>
              <li>• Push to SAP/Jira</li>
              <li>• Escalate incidents</li>
            </ul>
          </div>
          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium mb-2">Admin</h4>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>• All permissions</li>
              <li>• Manage integrations</li>
              <li>• Configure AI settings</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
