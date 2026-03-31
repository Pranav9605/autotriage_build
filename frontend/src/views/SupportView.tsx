import { useState, useMemo } from 'react';
import { IncidentFilters } from '@/components/support/IncidentFilters';
import { SupportIncidentList } from '@/components/support/SupportIncidentList';
import { SupportConsolePanel } from '@/components/support/SupportConsolePanel';
import { useIncidents } from '@/context/IncidentContext';
import type { Priority, Source } from '@/context/IncidentContext';
import { cn } from '@/lib/utils';

export function SupportView() {
  const { state } = useIncidents();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState<Source[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<Priority[]>([]);
  const [minConfidence, setMinConfidence] = useState(0);

  const filteredIncidents = useMemo(() => {
    return state.incidents.filter((incident) => {
      // Search filter
      if (search) {
        const searchLower = search.toLowerCase();
        const matchesSearch = 
          incident.id.toLowerCase().includes(searchLower) ||
          incident.shortText.toLowerCase().includes(searchLower) ||
          incident.longText.toLowerCase().includes(searchLower) ||
          (incident.errorCode?.toLowerCase().includes(searchLower) ?? false);
        if (!matchesSearch) return false;
      }

      // Source filter
      if (sourceFilter.length > 0 && !sourceFilter.includes(incident.source)) {
        return false;
      }

      // Priority filter
      if (priorityFilter.length > 0 && !priorityFilter.includes(incident.priority)) {
        return false;
      }

      // Confidence filter
      if (incident.confidence < minConfidence) {
        return false;
      }

      return true;
    });
  }, [state.incidents, search, sourceFilter, priorityFilter, minConfidence]);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredIncidents.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredIncidents.map(inc => inc.id));
    }
  };

  return (
    <div className={cn(
      "flex flex-col h-full",
      state.isFullScreen && "fixed inset-0 z-50 bg-background"
    )}>
      <IncidentFilters
        onSearchChange={setSearch}
        onSourceFilter={setSourceFilter as any}
        onPriorityFilter={setPriorityFilter}
        onConfidenceFilter={setMinConfidence}
      />
      <div className="flex flex-1 min-h-0">
        {/* 50% Incident List */}
        <div className="w-1/2 flex flex-col">
          <SupportIncidentList
            incidents={filteredIncidents}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onSelectAll={handleSelectAll}
          />
        </div>
        {/* 50% Support Console */}
        <div className="w-1/2 flex flex-col">
          <SupportConsolePanel />
        </div>
      </div>
    </div>
  );
}
