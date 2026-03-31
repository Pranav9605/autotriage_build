import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { api, KBArticle } from '@/services/api';
import { mapPriorityFromBackend, mapPriorityToBackend } from '@/utils/priorityMapping';
import {
  BookOpen,
  Plus,
  Search,
  Trash2,
  FileText,
  TrendingUp,
  Loader2,
  AlertCircle
} from 'lucide-react';
import type { Priority } from '@/data/mockData';

const CATEGORIES = [
  'FI - Finance',
  'MM - Materials',
  'SD - Sales',
  'BASIS - System',
  'ABAP - Development',
  'PI_PO - Integration',
  'PP - Production'
];

const PRIORITIES = ['Critical', 'High', 'Medium', 'Low'];

export function KnowledgeBaseView() {
  const [articles, setArticles] = useState<KBArticle[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({ total_articles: 0, total_hits: 0 });

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    problem: '',
    solution: '',
    category: CATEGORIES[0],
    priority: PRIORITIES[2]
  });

  const fetchArticles = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listKBArticles();
      setArticles(data);
    } catch (err) {
      // Silently handle - backend may not be running
      console.warn('KB articles fetch failed - backend may be offline');
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const pipelineStats = await api.getPipelineStats();
      setStats(pipelineStats.knowledge_base);
    } catch (err) {
      // Silently handle - show zeros if backend unavailable
      console.warn('Pipeline stats fetch failed - backend may be offline');
    }
  };

  useEffect(() => {
    fetchArticles();
    fetchStats();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await api.addKBArticle({
        title: formData.title,
        problem: formData.problem,
        solution: formData.solution,
        category: formData.category,
        priority: formData.priority
      });
      setFormData({
        title: '',
        problem: '',
        solution: '',
        category: CATEGORIES[0],
        priority: PRIORITIES[2]
      });
      fetchArticles();
      fetchStats();
    } catch (err) {
      setError('Failed to add article');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (articleId: string) => {
    if (!articleId) return;
    try {
      await api.deleteKBArticle(articleId);
      fetchArticles();
      fetchStats();
    } catch (err) {
      setError('Failed to delete article');
      console.error(err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchArticles();
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const results = await api.searchKB(searchQuery);
      setArticles(results);
    } catch (err) {
      setError('Search failed');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredArticles = articles;

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary" />
            Knowledge Base
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage KB articles for semantic matching and instant resolution
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 max-w-md">
        <div className="kpi-card">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <FileText className="w-4 h-4" />
            Total Articles
          </div>
          <p className="text-2xl font-bold mt-1">{stats.total_articles}</p>
        </div>
        <div className="kpi-card">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <TrendingUp className="w-4 h-4" />
            Total Hits
          </div>
          <p className="text-2xl font-bold mt-1">{stats.total_hits}</p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add Article Form */}
        <div className="kpi-card">
          <div className="flex items-center gap-2 mb-4">
            <Plus className="w-5 h-5 text-primary" />
            <h2>Add New Article</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Enter article title..."
                required
              />
            </div>

            <div>
              <Label htmlFor="problem">Problem Description</Label>
              <Textarea
                id="problem"
                value={formData.problem}
                onChange={(e) => setFormData({ ...formData, problem: e.target.value })}
                placeholder="Describe the problem (used for semantic matching)..."
                rows={3}
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                This text is used for semantic matching when tickets come in
              </p>
            </div>

            <div>
              <Label htmlFor="solution">Solution</Label>
              <Textarea
                id="solution"
                value={formData.solution}
                onChange={(e) => setFormData({ ...formData, solution: e.target.value })}
                placeholder="Describe the solution..."
                rows={3}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category">Category</Label>
                <select
                  id="category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-border rounded-md text-sm bg-background"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <Label htmlFor="priority">Priority</Label>
                <select
                  id="priority"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-border rounded-md text-sm bg-background"
                >
                  {PRIORITIES.map((pri) => (
                    <option key={pri} value={pri}>{pri}</option>
                  ))}
                </select>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Article
                </>
              )}
            </Button>
          </form>
        </div>

        {/* Articles List */}
        <div className="kpi-card">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-primary" />
            <h2>Articles</h2>
          </div>

          {/* Search */}
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Search articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button variant="outline" onClick={handleSearch}>
              <Search className="w-4 h-4" />
            </Button>
          </div>

          {/* List */}
          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredArticles.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No articles found
              </div>
            ) : (
              filteredArticles.map((article) => (
                <div
                  key={article.article_id}
                  className="p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm truncate">{article.title}</h4>
                        <PriorityBadge 
                          priority={mapPriorityFromBackend(article.priority) as Priority} 
                          size="sm" 
                        />
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-1">
                        {article.problem}
                      </p>
                      <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                        {article.category}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={() => article.article_id && handleDelete(article.article_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
