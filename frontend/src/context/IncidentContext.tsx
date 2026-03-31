import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';

export type Priority = 'P1' | 'P2' | 'P3' | 'P4';
export type Source = 'WhatsApp' | 'Jira' | 'Email' | 'Phone' | 'Chat' | 'SolMan' | 'PI_PO';
export type Status = 'New' | 'In Progress' | 'Pending' | 'Resolved';
export type AISource = 'ml' | 'kb' | 'cache' | 'llm';

export interface Incident {
  id: string;
  shortText: string;
  longText: string;
  source: Source;
  priority: Priority;
  status: Status;
  issueType: string;
  severity: Priority;
  rootCause: string;
  suggestedTeam: string;
  assignedTeam: string | null;
  sapModule: string;
  confidence: number;
  createdAt: Date;
  updatedAt: Date;
  age: string;
  assignee: string | null;
  hasMedia: boolean;
  mediaType?: 'image' | 'video' | 'document' | 'audio';
  mediaUrl?: string;
  aiSummary: string;
  aiBullets: string[];
  aiRationale: string;
  aiSolution: string;
  errorCode?: string;
  aiSource?: AISource;
  tcode?: string;
  environment?: 'PRD' | 'QAS' | 'DEV';
  manual_review_required?: boolean;
  similarTickets?: { id: string; match: number }[];
  notes: string[];
  chatHistory?: ChatMessage[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  mediaType?: 'image' | 'audio' | 'text';
  mediaUrl?: string;
}

interface IncidentState {
  incidents: Incident[];
  selectedIncidentId: string | null;
  isFullScreen: boolean;
}

type IncidentAction =
  | { type: 'ADD_INCIDENT'; payload: Incident }
  | { type: 'UPDATE_INCIDENT'; payload: { id: string; updates: Partial<Incident> } }
  | { type: 'DELETE_INCIDENT'; payload: string }
  | { type: 'SELECT_INCIDENT'; payload: string | null }
  | { type: 'SET_FULLSCREEN'; payload: boolean }
  | { type: 'ADD_NOTE'; payload: { id: string; note: string } }
  | { type: 'ADD_CHAT_MESSAGE'; payload: { id: string; message: ChatMessage } }
  | { type: 'SET_INCIDENTS'; payload: Incident[] };

const initialIncidents: Incident[] = [
  {
    id: 'INC-2024-001',
    shortText: 'getting error while posting vendor invoice in production',
    longText: 'User reports F5 301 error when trying to post a vendor invoice via FB50 in production. Document type assignment appears to be missing for the posting key in the target company code. Multiple finance users affected and month-end close is approaching.',
    source: 'WhatsApp',
    priority: 'P2',
    status: 'New',
    issueType: 'FI - Finance',
    severity: 'P2',
    rootCause: 'Document type configuration missing for posting key in target company code',
    suggestedTeam: 'SAP Finance Team',
    assignedTeam: null,
    sapModule: 'FI',
    tcode: 'FB50',
    environment: 'PRD',
    confidence: 85,
    manual_review_required: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 45),
    updatedAt: new Date(Date.now() - 1000 * 60 * 10),
    age: '45m',
    assignee: null,
    hasMedia: false,
    aiSummary: 'F5 301 error on FB50 vendor invoice posting — document type config issue in company code',
    aiBullets: [
      'Error F5 301 indicates missing document type assignment for posting key',
      'Check OBA7 for document type configuration in the company code',
      'Verify posting key 40/50 config in FS00 for the GL account',
      'Validate company code fiscal year settings in OB29'
    ],
    aiRationale: 'High confidence based on specific error code F5 301 and FB50 transaction context',
    aiSolution: 'Check OBA7 for document type assignment. Verify posting key 40/50 config in FS00 for the GL account. Validate company code settings in OB29.',
    errorCode: 'F5 301',
    aiSource: 'ml',
    similarTickets: [{ id: 'INC-2023-087', match: 92 }, { id: 'INC-2023-045', match: 87 }],
    notes: []
  },
  {
    id: 'INC-2024-002',
    shortText: 'system dump on production — users cannot log in',
    longText: 'Critical P1: ABAP runtime error causing system dump on production. Multiple users unable to log in. Error logged in SM21 system log. Issue started at 08:30 IST. Approximately 250 concurrent users impacted. BASIS team notified.',
    source: 'SolMan',
    priority: 'P1',
    status: 'In Progress',
    issueType: 'BASIS - System',
    severity: 'P1',
    rootCause: 'ABAP runtime error in core login processing program',
    suggestedTeam: 'BASIS Team',
    assignedTeam: 'BASIS Team',
    sapModule: 'BASIS',
    tcode: 'SM21',
    environment: 'PRD',
    confidence: 91,
    manual_review_required: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 90),
    updatedAt: new Date(Date.now() - 1000 * 60 * 5),
    age: '1.5h',
    assignee: 'Rajesh Kumar',
    hasMedia: false,
    aiSummary: 'Critical ABAP runtime dump preventing user login on PRD — SM21 shows core dump in login programme',
    aiBullets: [
      'Check ST22 for latest short dump details and failing programme',
      'Review SM21 system log for root cause time correlation',
      'Verify recent transports via STMS — dump may be transport-related',
      'Consider emergency rollback if transport-related'
    ],
    aiRationale: 'Critical PRD+P1 — manual review mandatory per policy even at 91% confidence',
    aiSolution: 'Analyse ST22 dump and identify the failing programme. Check recent transport imports via STMS. Rollback if transport-related. Engage SAP support if core system issue.',
    errorCode: 'ABAP_RUNTIME_ERROR',
    aiSource: 'ml',
    similarTickets: [{ id: 'INC-2023-112', match: 88 }, { id: 'INC-2023-098', match: 81 }],
    notes: ['Rajesh investigating ST22 dump', 'Emergency bridge call at 10:00 AM']
  },
  {
    id: 'INC-2024-003',
    shortText: 'purchase order creation failing in QAS since yesterday',
    longText: "Users report M7 021 error when creating purchase orders in ME21N in QAS. Issue started after yesterday's batch of transports. Multiple buyers blocked from testing for UAT sign-off.",
    source: 'Email',
    priority: 'P3',
    status: 'New',
    issueType: 'MM - Materials',
    severity: 'P3',
    rootCause: 'Material master or plant configuration missing after transport',
    suggestedTeam: 'SAP MM Team',
    assignedTeam: null,
    sapModule: 'MM',
    tcode: 'ME21N',
    environment: 'QAS',
    confidence: 78,
    manual_review_required: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 120),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60),
    age: '2h',
    assignee: null,
    hasMedia: false,
    aiSummary: 'M7 021 error on ME21N in QAS — likely plant or material config missing post-transport',
    aiBullets: [
      'M7 021 indicates plant/material configuration mismatch',
      'Check MARC table for material-plant assignment in QAS',
      "Review STMS transport log for yesterday's imports",
      'Validate purchasing organisation settings in OME1'
    ],
    aiRationale: 'QAS issue likely transport-related — verify config completeness across client',
    aiSolution: 'Check material master in MM60 for the affected plant. Validate purchasing org in OME1. Re-transport missing customising if identified.',
    errorCode: 'M7 021',
    aiSource: 'kb',
    similarTickets: [{ id: 'INC-2024-008', match: 79 }, { id: 'INC-2023-201', match: 74 }],
    notes: []
  },
  {
    id: 'INC-2024-004',
    shortText: 'custom report throwing dump after transport',
    longText: 'Custom ABAP report ZMM_STOCK_REPORT_01 throwing SYNTAX_ERROR dump immediately after the latest transport from DEV to QAS. Developers need this fixed in DEV before the next transport window.',
    source: 'Chat',
    priority: 'P2',
    status: 'Pending',
    issueType: 'ABAP - Development',
    severity: 'P2',
    rootCause: 'Syntax error in custom report introduced during recent development',
    suggestedTeam: 'ABAP Dev Team',
    assignedTeam: null,
    sapModule: 'ABAP',
    tcode: 'SE38',
    environment: 'DEV',
    confidence: 62,
    manual_review_required: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 3),
    updatedAt: new Date(Date.now() - 1000 * 60 * 45),
    age: '3h',
    assignee: null,
    hasMedia: false,
    aiSummary: 'Syntax error dump on ZMM_STOCK_REPORT_01 in DEV — manual review required due to low confidence (62%)',
    aiBullets: [
      'Check SE38 for syntax errors in ZMM_STOCK_REPORT_01',
      'Review ST22 for full dump trace and programme stack',
      'Verify all includes and function modules are active',
      'Check for missing TYPE-POOL or TABLES declarations'
    ],
    aiRationale: 'Lower confidence (62%) — custom code requires developer source review. Manual review flagged.',
    aiSolution: 'Open SE38 → ZMM_STOCK_REPORT_01 → Syntax Check (Ctrl+F2). Fix highlighted syntax errors. Activate and test with F8.',
    errorCode: 'SYNTAX_ERROR',
    aiSource: 'llm',
    similarTickets: [{ id: 'INC-2023-156', match: 71 }, { id: 'INC-2023-134', match: 68 }],
    notes: ['Waiting for developer to review SE38']
  },
  {
    id: 'INC-2024-005',
    shortText: 'sales order not saving — blocking entire order entry team',
    longText: 'Critical P1: Sales order creation via VA01 failing with V1 801 error in production. Entire order entry team of 35 users is blocked. Error occurs at the point of saving the order. Issue started at 09:15 IST today.',
    source: 'Jira',
    priority: 'P1',
    status: 'In Progress',
    issueType: 'SD - Sales',
    severity: 'P1',
    rootCause: 'Pricing procedure or condition type misconfiguration affecting sales order save',
    suggestedTeam: 'SAP SD Team',
    assignedTeam: 'SAP SD Team',
    sapModule: 'SD',
    tcode: 'VA01',
    environment: 'PRD',
    confidence: 88,
    manual_review_required: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
    updatedAt: new Date(Date.now() - 1000 * 60 * 15),
    age: '2h',
    assignee: 'Priya Sharma',
    hasMedia: false,
    aiSummary: 'V1 801 error blocking VA01 sales order save in PRD — pricing procedure or condition type issue',
    aiBullets: [
      'V1 801 typically indicates output or pricing procedure error at save',
      'Check VK13 for condition record validity dates',
      'Verify pricing procedure assignment in OVKK for the sales area',
      'Review output determination in NACE for sales order type'
    ],
    aiRationale: 'High confidence at 88% — PRD+P1 mandates manual review approval before action',
    aiSolution: 'Check pricing procedure assignment in OVKK. Verify condition records in VK13. If output-related, check NACE configuration for the order type.',
    errorCode: 'V1 801',
    aiSource: 'ml',
    similarTickets: [{ id: 'INC-2023-089', match: 85 }, { id: 'INC-2023-177', match: 77 }],
    notes: ['Priya on call with SAP SD team', 'Escalated to L2 at 10:00 AM']
  },
  {
    id: 'INC-2024-006',
    shortText: 'IDocs stuck in SM58 since morning, integration to WMS failing',
    longText: 'Outbound IDocs to the Warehouse Management System (WMS) stuck in SM58 with IDOC_ERROR status since 07:00 IST. Approximately 140 IDocs queued. PI/PO integration not processing them. Supplier delivery confirmations impacted.',
    source: 'WhatsApp',
    priority: 'P3',
    status: 'New',
    issueType: 'PI_PO - Integration',
    severity: 'P3',
    rootCause: 'IDocs stuck in outbound queue — likely partner profile or RFC destination issue in PI/PO',
    suggestedTeam: 'Integration Team',
    assignedTeam: null,
    sapModule: 'PI_PO',
    tcode: 'SXMB_MONI',
    environment: 'PRD',
    confidence: 71,
    manual_review_required: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5),
    updatedAt: new Date(Date.now() - 1000 * 60 * 120),
    age: '5h',
    assignee: null,
    hasMedia: false,
    aiSummary: '~140 outbound IDocs stuck in SM58 — PI/PO integration to WMS failing since 07:00 IST',
    aiBullets: [
      'Check SXMB_MONI for failed messages and error details',
      'Review WE20 partner profile for WMS partner configuration',
      'Validate RFC destination in SM59 for PI/PO connection',
      'Check SM58 transactional RFC queue for full backlog'
    ],
    aiRationale: 'Moderate confidence — PI/PO issues require integration team validation of channel config',
    aiSolution: 'Open SXMB_MONI → check failed messages. Review SM59 RFC destination for WMS. Validate WE20 partner profile. Restart PI/PO channel if RFC is healthy.',
    errorCode: 'IDOC_ERROR',
    aiSource: 'kb',
    similarTickets: [{ id: 'INC-2023-178', match: 83 }, { id: 'INC-2023-167', match: 76 }],
    notes: []
  }
];

const initialState: IncidentState = {
  incidents: initialIncidents,
  selectedIncidentId: null,
  isFullScreen: false
};

function incidentReducer(state: IncidentState, action: IncidentAction): IncidentState {
  switch (action.type) {
    case 'ADD_INCIDENT':
      return {
        ...state,
        incidents: [action.payload, ...state.incidents]
      };
    case 'UPDATE_INCIDENT':
      return {
        ...state,
        incidents: state.incidents.map(inc =>
          inc.id === action.payload.id
            ? { ...inc, ...action.payload.updates, updatedAt: new Date() }
            : inc
        )
      };
    case 'DELETE_INCIDENT':
      return {
        ...state,
        incidents: state.incidents.filter(inc => inc.id !== action.payload),
        selectedIncidentId: state.selectedIncidentId === action.payload ? null : state.selectedIncidentId
      };
    case 'SELECT_INCIDENT':
      return {
        ...state,
        selectedIncidentId: action.payload
      };
    case 'SET_FULLSCREEN':
      return {
        ...state,
        isFullScreen: action.payload
      };
    case 'ADD_NOTE':
      return {
        ...state,
        incidents: state.incidents.map(inc =>
          inc.id === action.payload.id
            ? { ...inc, notes: [...inc.notes, action.payload.note], updatedAt: new Date() }
            : inc
        )
      };
    case 'ADD_CHAT_MESSAGE':
      return {
        ...state,
        incidents: state.incidents.map(inc =>
          inc.id === action.payload.id
            ? { 
                ...inc, 
                chatHistory: [...(inc.chatHistory || []), action.payload.message],
                updatedAt: new Date()
              }
            : inc
        )
      };
    case 'SET_INCIDENTS':
      return {
        ...state,
        incidents: action.payload
      };
    default:
      return state;
  }
}

interface IncidentContextType {
  state: IncidentState;
  addIncident: (incident: Incident) => void;
  updateIncident: (id: string, updates: Partial<Incident>) => void;
  deleteIncident: (id: string) => void;
  selectIncident: (id: string | null) => void;
  setFullScreen: (value: boolean) => void;
  addNote: (id: string, note: string) => void;
  addChatMessage: (id: string, message: ChatMessage) => void;
  getSelectedIncident: () => Incident | null;
  createIncidentFromChat: (data: Partial<Incident>) => Incident;
}

const IncidentContext = createContext<IncidentContextType | null>(null);

export function IncidentProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(incidentReducer, initialState);

  const addIncident = useCallback((incident: Incident) => {
    dispatch({ type: 'ADD_INCIDENT', payload: incident });
  }, []);

  const updateIncident = useCallback((id: string, updates: Partial<Incident>) => {
    dispatch({ type: 'UPDATE_INCIDENT', payload: { id, updates } });
  }, []);

  const deleteIncident = useCallback((id: string) => {
    dispatch({ type: 'DELETE_INCIDENT', payload: id });
  }, []);

  const selectIncident = useCallback((id: string | null) => {
    dispatch({ type: 'SELECT_INCIDENT', payload: id });
  }, []);

  const setFullScreen = useCallback((value: boolean) => {
    dispatch({ type: 'SET_FULLSCREEN', payload: value });
  }, []);

  const addNote = useCallback((id: string, note: string) => {
    dispatch({ type: 'ADD_NOTE', payload: { id, note } });
  }, []);

  const addChatMessage = useCallback((id: string, message: ChatMessage) => {
    dispatch({ type: 'ADD_CHAT_MESSAGE', payload: { id, message } });
  }, []);

  const getSelectedIncident = useCallback(() => {
    return state.incidents.find(inc => inc.id === state.selectedIncidentId) || null;
  }, [state.incidents, state.selectedIncidentId]);

  const createIncidentFromChat = useCallback((data: Partial<Incident>): Incident => {
    const id = `INC-${new Date().getFullYear()}-${String(state.incidents.length + 1).padStart(3, '0')}`;
    const now = new Date();
    const incident: Incident = {
      id,
      shortText: data.shortText || 'New incident from chat',
      longText: data.longText || '',
      source: 'Chat',
      priority: data.priority || 'P3',
      status: 'New',
      issueType: data.issueType || 'Technical Issue',
      severity: data.severity || 'P3',
      rootCause: data.rootCause || '',
      suggestedTeam: data.suggestedTeam || '',
      assignedTeam: data.assignedTeam || null,
      sapModule: data.sapModule || '',
      confidence: data.confidence || 0,
      createdAt: now,
      updatedAt: now,
      age: '0m',
      assignee: data.assignee || null,
      hasMedia: data.hasMedia || false,
      mediaType: data.mediaType,
      mediaUrl: data.mediaUrl,
      aiSummary: data.aiSummary || '',
      aiBullets: data.aiBullets || [],
      aiRationale: data.aiRationale || '',
      aiSolution: data.aiSolution || '',
      errorCode: data.errorCode,
      aiSource: data.aiSource,
      tcode: data.tcode,
      environment: data.environment,
      manual_review_required: data.manual_review_required ?? false,
      similarTickets: data.similarTickets || [],
      notes: data.notes || [],
      chatHistory: data.chatHistory || []
    };
    dispatch({ type: 'ADD_INCIDENT', payload: incident });
    dispatch({ type: 'SELECT_INCIDENT', payload: id });
    return incident;
  }, [state.incidents.length]);

  return (
    <IncidentContext.Provider value={{
      state,
      addIncident,
      updateIncident,
      deleteIncident,
      selectIncident,
      setFullScreen,
      addNote,
      addChatMessage,
      getSelectedIncident,
      createIncidentFromChat
    }}>
      {children}
    </IncidentContext.Provider>
  );
}

export function useIncidents() {
  const context = useContext(IncidentContext);
  if (!context) {
    throw new Error('useIncidents must be used within an IncidentProvider');
  }
  return context;
}
