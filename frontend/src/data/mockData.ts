export type Priority = 'P1' | 'P2' | 'P3' | 'P4';
export type Source = 'WhatsApp' | 'Jira' | 'Email' | 'Phone';
export type Status = 'New' | 'In Progress' | 'Pending' | 'Resolved';

export interface Incident {
  id: string;
  shortText: string;
  longText: string;
  source: Source;
  priority: Priority;
  status: Status;
  suggestedPriority: Priority;
  suggestedTeam: string;
  suggestedCategory: string;
  sapModule: string;
  confidence: number;
  createdAt: Date;
  updatedAt: Date;
  age: string;
  assignee: string | null;
  hasMedia: boolean;
  mediaType?: 'image' | 'video' | 'document';
  aiSummary: string;
  aiBullets: string[];
  aiRationale: string;
  errorCode?: string;
  aiSource?: 'ml' | 'kb' | 'cache' | 'llm';
}

export const mockIncidents: Incident[] = [
  {
    id: 'INC-2024-001',
    shortText: 'SAP FI posting error - GL account blocked',
    longText: 'User reports that when attempting to post a journal entry in transaction FB50, the system returns error message "Account 400100 is blocked for posting". This is impacting month-end close activities.',
    source: 'WhatsApp',
    priority: 'P1',
    status: 'New',
    suggestedPriority: 'P1',
    suggestedTeam: 'SAP Finance',
    suggestedCategory: 'GL Posting',
    sapModule: 'FI',
    confidence: 94,
    createdAt: new Date(Date.now() - 1000 * 60 * 45),
    updatedAt: new Date(Date.now() - 1000 * 60 * 10),
    age: '45m',
    assignee: null,
    hasMedia: true,
    mediaType: 'image',
    aiSummary: 'GL account 400100 blocked preventing FI postings during month-end close',
    aiBullets: [
      'Error occurs in FB50 transaction',
      'Account 400100 is flagged as blocked',
      'Impacting critical month-end activities',
      'Likely needs master data team intervention'
    ],
    aiRationale: 'High confidence based on clear error message and business impact during close period',
    errorCode: 'F5 301',
    aiSource: 'ml'
  },
  {
    id: 'INC-2024-002',
    shortText: 'MM Purchase Order approval workflow stuck',
    longText: 'Multiple POs in the approval queue are not progressing. Approvers report they cannot see pending items in their worklist. Last successful approval was 3 hours ago.',
    source: 'Jira',
    priority: 'P2',
    status: 'In Progress',
    suggestedPriority: 'P2',
    suggestedTeam: 'SAP MM/Workflow',
    suggestedCategory: 'Workflow',
    sapModule: 'MM',
    confidence: 88,
    createdAt: new Date(Date.now() - 1000 * 60 * 180),
    updatedAt: new Date(Date.now() - 1000 * 60 * 30),
    age: '3h',
    assignee: 'Rajesh Kumar',
    hasMedia: false,
    aiSummary: 'PO approval workflow halted - approvers cannot see worklist items',
    aiBullets: [
      'Workflow engine may need restart',
      'Check SWI2_FREQ for stuck work items',
      'Verify approver substitution rules',
      'Background job SWWDHEX might be inactive'
    ],
    aiRationale: 'Pattern matches common workflow blockage scenarios in MM module',
    errorCode: 'WF-STUCK',
    aiSource: 'kb'
  },
  {
    id: 'INC-2024-003',
    shortText: 'SD Billing document output not generated',
    longText: 'Customer invoices created today are not generating PDF output. Print queue shows documents as pending but no actual output is being produced.',
    source: 'Email',
    priority: 'P2',
    status: 'New',
    suggestedPriority: 'P2',
    suggestedTeam: 'SAP SD/Output',
    suggestedCategory: 'Output Management',
    sapModule: 'SD',
    confidence: 91,
    createdAt: new Date(Date.now() - 1000 * 60 * 120),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60),
    age: '2h',
    assignee: null,
    hasMedia: true,
    mediaType: 'image',
    aiSummary: 'Billing document PDF generation failing - output queue blocked',
    aiBullets: [
      'Check spool processor status',
      'Verify output type ZNEW configuration',
      'Review NAST table for pending outputs',
      'Smart Forms runtime may need restart'
    ],
    aiRationale: 'Clear output management issue affecting customer-facing invoices',
    aiSource: 'cache'
  },
  {
    id: 'INC-2024-004',
    shortText: 'Basis - System performance degradation',
    longText: 'Users across all modules reporting slow response times. Dialog work processes showing high CPU utilization. Issue started after last night batch job completion.',
    source: 'Phone',
    priority: 'P1',
    status: 'In Progress',
    suggestedPriority: 'P1',
    suggestedTeam: 'SAP Basis',
    suggestedCategory: 'Performance',
    sapModule: 'Basis',
    confidence: 96,
    createdAt: new Date(Date.now() - 1000 * 60 * 90),
    updatedAt: new Date(Date.now() - 1000 * 60 * 5),
    age: '1.5h',
    assignee: 'Priya Sharma',
    hasMedia: false,
    aiSummary: 'System-wide performance issue after batch job - high CPU on dialog WPs',
    aiBullets: [
      'Check ST03N for transaction response times',
      'Review SM66 for long-running processes',
      'Batch job may have caused table locks',
      'Consider buffer refresh if tables were mass-updated'
    ],
    aiRationale: 'Critical P1 due to system-wide impact with clear correlation to batch processing',
    aiSource: 'llm'
  },
  {
    id: 'INC-2024-005',
    shortText: 'Integration - IDoc processing errors to external system',
    longText: 'Outbound IDocs to vendor EDI system failing with status 03. Error indicates partner profile issue. Affecting supplier order confirmations.',
    source: 'Jira',
    priority: 'P3',
    status: 'Pending',
    suggestedPriority: 'P3',
    suggestedTeam: 'Integration',
    suggestedCategory: 'EDI/IDoc',
    sapModule: 'Integration',
    confidence: 85,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5),
    updatedAt: new Date(Date.now() - 1000 * 60 * 120),
    age: '5h',
    assignee: 'Amit Patel',
    hasMedia: true,
    mediaType: 'document',
    aiSummary: 'IDoc status 03 errors - partner profile configuration issue',
    aiBullets: [
      'Review WE20 partner profile settings',
      'Check port configuration in WE21',
      'Verify message type assignment',
      'May need RFC destination validation'
    ],
    aiRationale: 'Standard IDoc troubleshooting pattern with partner profile focus',
    aiSource: 'ml'
  },
  {
    id: 'INC-2024-006',
    shortText: 'Custom ABAP program dump in production',
    longText: 'Custom report ZCUSTOM_SALES_01 throwing runtime error GETWA_NOT_ASSIGNED when executed with large date ranges. Users need this for quarterly reporting.',
    source: 'WhatsApp',
    priority: 'P3',
    status: 'New',
    suggestedPriority: 'P2',
    suggestedTeam: 'Custom Development',
    suggestedCategory: 'ABAP',
    sapModule: 'Custom',
    confidence: 72,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
    updatedAt: new Date(Date.now() - 1000 * 60 * 30),
    age: '2h',
    assignee: null,
    hasMedia: true,
    mediaType: 'image',
    aiSummary: 'Custom report ZCUSTOM_SALES_01 dumps with GETWA_NOT_ASSIGNED on large selections',
    aiBullets: [
      'Check ST22 for full dump analysis',
      'Internal table access without prior READ likely',
      'May need index optimization for large ranges',
      'Consider background execution for big data'
    ],
    aiRationale: 'Lower confidence - custom code requires developer analysis of source',
    aiSource: 'llm'
  }
];

export const kpiData = {
  openTickets: 23,
  openTicketsTrend: 3,
  slaBreaches: 2,
  slaBreachesTrend: -1,
  avgTimeToAssignment: '4.2 min',
  assignmentTrend: -8,
  mttr: '3.8h',
  mttrTrend: -15,
  suggestionsAccepted: 81,
  acceptedTrend: 5,
};

export const incidentsBySource = [
  { name: 'WhatsApp', value: 35, color: '#25D366' },
  { name: 'SolMan', value: 28, color: '#0078D4' },
  { name: 'Email', value: 20, color: '#EA4335' },
  { name: 'Jira', value: 12, color: '#0052CC' },
  { name: 'Chat', value: 5, color: '#7B5EA7' }
];

export const volumeTrend = [
  { date: 'Mon', incidents: 42 },
  { date: 'Tue', incidents: 38 },
  { date: 'Wed', incidents: 55 },
  { date: 'Thu', incidents: 47 },
  { date: 'Fri', incidents: 62 },
  { date: 'Sat', incidents: 23 },
  { date: 'Sun', incidents: 18 },
];

export const topCategories = [
  { category: 'FI', count: 30, color: '#3B82F6' },
  { category: 'BASIS', count: 20, color: '#EF4444' },
  { category: 'MM', count: 15, color: '#F97316' },
  { category: 'SD', count: 15, color: '#22C55E' },
  { category: 'PI_PO', count: 10, color: '#EAB308' },
  { category: 'ABAP', count: 10, color: '#A855F7' }
];

export const priorityByTeam = [
  { team: 'SAP Finance', P1: 2, P2: 5, P3: 8, P4: 3 },
  { team: 'SAP MM', P1: 1, P2: 4, P3: 6, P4: 4 },
  { team: 'SAP SD', P1: 0, P2: 3, P3: 5, P4: 2 },
  { team: 'Basis', P1: 3, P2: 2, P3: 4, P4: 1 },
  { team: 'Integration', P1: 1, P2: 3, P3: 3, P4: 5 },
];

export const integrationHealth = [
  { name: 'WhatsApp', status: 'healthy', lastSync: '2 min ago' },
  { name: 'Jira', status: 'healthy', lastSync: '1 min ago' },
  { name: 'SAP SolMan', status: 'warning', lastSync: '15 min ago' },
  { name: 'SAP CPI', status: 'healthy', lastSync: '30 sec ago' },
];

export const similarCases = [
  { id: 'INC-2023-892', title: 'GL posting blocked - cost center issue', resolution: 'Unblocked via FAGL_BLOCK_UNBLOCK', resolvedIn: '45m' },
  { id: 'INC-2023-756', title: 'Account blocked for posting', resolution: 'Master data team updated account flags', resolvedIn: '1.2h' },
  { id: 'INC-2024-034', title: 'FB50 error on intercompany posting', resolution: 'Trading partner config corrected', resolvedIn: '2h' },
];

export const kbArticles = [
  { id: 'KB-001', title: 'How to unblock GL accounts for posting', views: 1234 },
  { id: 'SAP-2847291', title: 'Account blocked for posting in new GL', views: 892 },
  { id: 'KB-045', title: 'Month-end close checklist for FI', views: 567 },
];
