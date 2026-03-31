import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import type { Source, Priority } from '@/data/mockData';

interface IncidentFiltersProps {
  onSearchChange: (search: string) => void;
  onSourceFilter: (sources: Source[]) => void;
  onPriorityFilter: (priorities: Priority[]) => void;
  onConfidenceFilter: (minConfidence: number) => void;
}

export function IncidentFilters({
  onSearchChange,
  onSourceFilter,
  onPriorityFilter,
  onConfidenceFilter,
}: IncidentFiltersProps) {
  const [selectedSources, setSelectedSources] = useState<Source[]>([]);
  const [selectedPriorities, setSelectedPriorities] = useState<Priority[]>([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState([0]);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const sources: Source[] = ['WhatsApp', 'Jira', 'Email', 'Phone'];
  const priorities: Priority[] = ['P1', 'P2', 'P3', 'P4'];
  const sapModules = ['FI', 'MM', 'SD', 'Basis', 'Integration', 'Custom'];
  const presets = [
    { id: 'my-tickets', label: 'My Tickets', count: 5 },
    { id: 'high-risk', label: 'High-Risk', count: 3 },
    { id: 'unassigned', label: 'Unassigned', count: 12 },
    { id: 'needs-review', label: 'Needs Review', count: 8 },
  ];

  const toggleSource = (source: Source) => {
    const newSources = selectedSources.includes(source)
      ? selectedSources.filter(s => s !== source)
      : [...selectedSources, source];
    setSelectedSources(newSources);
    onSourceFilter(newSources);
  };

  const togglePriority = (priority: Priority) => {
    const newPriorities = selectedPriorities.includes(priority)
      ? selectedPriorities.filter(p => p !== priority)
      : [...selectedPriorities, priority];
    setSelectedPriorities(newPriorities);
    onPriorityFilter(newPriorities);
  };

  const clearFilters = () => {
    setSelectedSources([]);
    setSelectedPriorities([]);
    setConfidenceThreshold([0]);
    setActivePreset(null);
    onSourceFilter([]);
    onPriorityFilter([]);
    onConfidenceFilter(0);
  };

  const hasActiveFilters = selectedSources.length > 0 || selectedPriorities.length > 0 || confidenceThreshold[0] > 0;

  return (
    <div className="bg-card/50 border-b border-border px-6 py-4 space-y-4">
      {/* Top Row: Search + Filter Button */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search tickets, errors, IDs..." 
            className="pl-10 bg-background border-border/60 h-10"
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2 h-10">
              <SlidersHorizontal className="w-4 h-4" />
              Advanced Filters
              {hasActiveFilters && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
                  {selectedSources.length + selectedPriorities.length + (confidenceThreshold[0] > 0 ? 1 : 0)}
                </span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80" align="end">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Advanced Filters</h4>
                {hasActiveFilters && (
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="h-7 text-xs">
                    Clear all
                  </Button>
                )}
              </div>

              {/* SAP Module */}
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase mb-2">SAP Module</p>
                <div className="flex flex-wrap gap-1.5">
                  {sapModules.map((module) => (
                    <button key={module} className="filter-chip text-xs">
                      {module}
                    </button>
                  ))}
                </div>
              </div>

              {/* Confidence Slider */}
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase mb-3">
                  Min Confidence: {confidenceThreshold[0]}%
                </p>
                <Slider
                  value={confidenceThreshold}
                  onValueChange={(value) => {
                    setConfidenceThreshold(value);
                    onConfidenceFilter(value[0]);
                  }}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>

              {/* Keyboard Shortcuts */}
              <div className="pt-3 border-t border-border">
                <p className="text-xs font-medium text-muted-foreground uppercase mb-2">Shortcuts</p>
                <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">C</kbd>
                    <span>Claim</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">A</kbd>
                    <span>Accept</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">E</kbd>
                    <span>Escalate</span>
                  </div>
                </div>
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1.5 text-muted-foreground h-10">
            <X className="w-3.5 h-3.5" />
            Clear
          </Button>
        )}
      </div>

      {/* Bottom Row: Filter Chips */}
      <div className="flex items-center gap-6 flex-wrap">
        {/* Quick Presets */}
        <div className="flex items-center gap-2">
          {presets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => setActivePreset(activePreset === preset.id ? null : preset.id)}
              className={cn(
                "filter-chip text-xs",
                activePreset === preset.id && "filter-chip-active"
              )}
            >
              {preset.label}
              <span className="text-[10px] opacity-70">{preset.count}</span>
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-border" />

        {/* Source Filters */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-medium">Source:</span>
          {sources.map((source) => (
            <button
              key={source}
              onClick={() => toggleSource(source)}
              className={cn(
                "filter-chip text-xs",
                selectedSources.includes(source) && "filter-chip-active"
              )}
            >
              {source}
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-border" />

        {/* Priority Filters */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-medium">Priority:</span>
          {priorities.map((priority) => (
            <button
              key={priority}
              onClick={() => togglePriority(priority)}
              className={cn(
                "filter-chip text-xs",
                selectedPriorities.includes(priority) && "filter-chip-active"
              )}
            >
              {priority}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
