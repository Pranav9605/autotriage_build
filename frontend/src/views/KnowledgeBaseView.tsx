import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { api, KBArticle } from '@/services/api';
import {
  BookOpen,
  Plus,
  Search,
  FileText,
  TrendingUp,
  Loader2,
  AlertCircle,
} from 'lucide-react';

const SAP_MODULES = ['FI', 'MM', 'SD', 'BASIS', 'ABAP', 'PI_PO', 'PP', 'HR', 'CUSTOM'];

export function KnowledgeBaseView() {
  const [articles, setArticles] = useState<KBArticle[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    title: '',
    content: '',
    module: SAP_MODULES[0],
    error_codes: '',
    tcodes: '',
    tags: '',
  });

  const fetchArticles = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listKBArticles();
      setArticles(data);
    } catch (err) {
      console.warn('KB articles fetch failed — backend may be offline');
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await api.createKBArticle({
        title: formData.title,
        content: formData.content,
        module: formData.module,
        error_codes: formData.error_codes ? formData.error_codes.split(',').map(s => s.trim()).filter(Boolean) : [],
        tcodes: formData.tcodes ? formData.tcodes.split(',').map(s => s.trim()).filter(Boolean) : [],
        tags: formData.tags ? formData.tags.split(',').map(s => s.trim()).filter(Boolean) : [],
      });
      setFormData({ title: '', content: '', module: SAP_MODULES[0], error_codes: '', tcodes: '', tags: '' });
      fetchArticles();
    } catch (err) {
      setError('Failed to add article. Is the backend running?');
      console.error(err);
    } finally {
      setIsSubmitting(false);
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
      const result = await api.searchKB(searchQuery);
      setArticles(result.results);
    } catch (err) {
      setError('Search failed. Is the backend running?');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

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
          <p className="text-2xl font-bold mt-1">{articles.length}</p>
        </div>
        <div className="kpi-card">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <TrendingUp className="w-4 h-4" />
            Modules Covered
          </div>
          <p className="text-2xl font-bold mt-1">
            {new Set(articles.map(a => a.module)).size}
          </p>
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
                placeholder="e.g. FB50 Posting Error F5 301"
                required
              />
            </div>

            <div>
              <Label htmlFor="content">Content</Label>
              <Textarea
                id="content"
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                placeholder="Problem description and solution steps (used for semantic matching)..."
                rows={4}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="module">SAP Module</Label>
                <select
                  id="module"
                  value={formData.module}
                  onChange={(e) => setFormData({ ...formData, module: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-border rounded-md text-sm bg-background"
                >
                  {SAP_MODULES.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="error_codes">Error Codes</Label>
                <Input
                  id="error_codes"
                  value={formData.error_codes}
                  onChange={(e) => setFormData({ ...formData, error_codes: e.target.value })}
                  placeholder="F5 301, M7 021 (comma-sep)"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="tcodes">T-Codes</Label>
                <Input
                  id="tcodes"
                  value={formData.tcodes}
                  onChange={(e) => setFormData({ ...formData, tcodes: e.target.value })}
                  placeholder="FB50, ME21N (comma-sep)"
                />
              </div>
              <div>
                <Label htmlFor="tags">Tags</Label>
                <Input
                  id="tags"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  placeholder="posting, fi, gl (comma-sep)"
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Adding...</>
              ) : (
                <><Plus className="w-4 h-4 mr-2" />Add Article</>
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

          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : articles.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No articles found
              </div>
            ) : (
              articles.map((article) => (
                <div
                  key={article.id}
                  className="p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm truncate">{article.title}</h4>
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded shrink-0">
                          {article.module}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-1">
                        {article.content}
                      </p>
                      {(article.error_codes?.length > 0 || article.tcodes?.length > 0) && (
                        <div className="flex gap-1 flex-wrap">
                          {article.error_codes?.slice(0, 2).map(ec => (
                            <span key={ec} className="text-xs bg-destructive/10 text-destructive px-1.5 py-0.5 rounded font-mono">
                              {ec}
                            </span>
                          ))}
                          {article.tcodes?.slice(0, 2).map(tc => (
                            <span key={tc} className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded font-mono">
                              {tc}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
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
