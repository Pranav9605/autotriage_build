// Backend uses Critical/High/Medium/Low, Frontend uses P1/P2/P3/P4

export const priorityToBackend: Record<string, string> = {
  'P1': 'Critical',
  'P2': 'High',
  'P3': 'Medium',
  'P4': 'Low'
};

export const priorityFromBackend: Record<string, string> = {
  'Critical': 'P1',
  'High': 'P2',
  'Medium': 'P3',
  'Low': 'P4'
};

export function mapPriorityToBackend(priority: string): string {
  return priorityToBackend[priority] || priority;
}

export function mapPriorityFromBackend(priority: string): string {
  return priorityFromBackend[priority] || priority;
}
