// Backend uses P1/P2/P3/P4 natively — these are pass-through helpers.
// Kept for call-site compatibility; no translation needed.

export function mapPriorityToBackend(priority: string): string {
  return priority;
}

export function mapPriorityFromBackend(priority: string): string {
  return priority;
}
