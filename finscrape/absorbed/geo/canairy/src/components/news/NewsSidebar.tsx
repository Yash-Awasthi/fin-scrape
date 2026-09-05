import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Newspaper,
  ExternalLink,
  Clock,
  AlertTriangle,
  X,
  RefreshCw,
  ChevronRight,
  Shield
} from 'lucide-react';
import { Badge } from '../core/Badge';
import { cn } from '../../utils/cn';
import { newsIntelligence } from '../../services/newsIntelligence';
import { formatDistanceToNow } from 'date-fns';
import { useStore } from '../../store';

interface NewsArticle {
  title: string;
  description: string;
  url: string;
  source: {
    id: string;
    name: string;
  };
  publishedAt: string;
  content: string;
  relevance_score?: number;
  source_credibility?: {
    score: number;
    bias: string;
    specialty?: string;
  };
  indicator_relevance?: string[];
}

interface NewsSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export const NewsSidebar: React.FC<NewsSidebarProps> = ({
  isOpen,
  onClose,
  className
}) => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedArticle, setExpandedArticle] = useState<number | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [refreshing, setRefreshing] = useState(false);
  
  const { indicators } = useStore();

  useEffect(() => {
    if (isOpen) {
      loadNews();
      
      // Set up auto-refresh every 5 minutes
      const refreshInterval = setInterval(() => {
        console.log('Auto-refreshing news sidebar...');
        loadNews();
      }, 5 * 60 * 1000); // 5 minutes
      
      return () => clearInterval(refreshInterval);
    }
  }, [isOpen]);

  const loadNews = async () => {
    try {
      setError(null);
      
      const newsArticles = await newsIntelligence.getGlobalNewsFeed(20);
      setArticles(newsArticles);
      setLastRefresh(new Date());
    } catch (err) {
      setError('Failed to load news articles');
      console.error('News sidebar error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadNews();
  };

  const getIndicatorStatus = (indicatorId: string) => {
    const indicator = indicators.find(i => i.id === indicatorId);
    return indicator?.status.level || 'unknown';
  };

  const getCredibilityColor = (score?: number) => {
    if (!score) return 'text-white/20';
    if (score >= 85) return 'text-green-400';
    if (score >= 70) return 'text-amber-400';
    return 'text-red-400';
  };

  const getIndicatorRelationshipText = (indicatorIds?: string[]) => {
    if (!indicatorIds || indicatorIds.length === 0) return 'General risk news';
    
    const texts: Record<string, string> = {
      treasury_tail: 'Banking system stress',
      taiwan_zone: 'Supply chain risk',
      vix_volatility: 'Market volatility',
      hormuz_war_risk: 'Energy supply risk',
      unemployment_rate: 'Economic stability',
      global_conflict_index: 'Geopolitical tension',
      ice_detention: 'Domestic control',
      mbridge_settlement: 'Dollar dominance'
    };
    
    return indicatorIds.map(id => texts[id] || 'Risk indicator').join(', ');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          className={cn(
            'fixed right-0 top-0 h-full bg-[#0E0E10]/95 backdrop-blur-xl border-l border-white/[0.04] z-30',
            'w-full sm:w-96', // Full width on mobile
            'flex flex-col shadow-2xl',
            className
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/[0.04]">
            <div className="flex items-center gap-3">
              <Newspaper className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-semibold text-white">Live News Feed</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="p-2 text-white/30 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                title="Refresh news"
              >
                <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              </button>
              <button
                onClick={onClose}
                className="p-2 text-white/30 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Last update time */}
          <div className="px-6 py-2 text-xs text-white/20 border-b border-white/[0.04]">
            Updated {formatDistanceToNow(lastRefresh, { addSuffix: true })}
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {loading ? (
              <div className="p-6 space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-white/[0.06] rounded w-1/2 mb-2"></div>
                    <div className="h-2 bg-white/[0.06] rounded w-1/4"></div>
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="p-6 text-center">
                <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <p className="text-white/30">{error}</p>
                <button
                  onClick={loadNews}
                  className="mt-4 px-4 py-2 bg-red-500/80 text-white rounded-lg hover:bg-red-500/90 transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : articles.length === 0 ? (
              <div className="p-6 text-center">
                <Newspaper className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/30">No news articles available</p>
              </div>
            ) : (
              <div className="divide-y divide-white/[0.04]">
                <AnimatePresence>
                  {articles.map((article, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-4 hover:bg-white/5 transition-colors cursor-pointer group"
                      onClick={() => setExpandedArticle(expandedArticle === index ? null : index)}
                    >
                      {/* Article header */}
                      <div className="mb-2">
                        <a
                          href={article.url !== '#' ? article.url : undefined}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className={article.url !== '#' ? 'hover:text-blue-400 transition-colors' : ''}
                        >
                          <h3 className="text-sm font-medium text-white line-clamp-2 mb-1">
                            {article.title}
                            {article.url !== '#' && (
                              <ExternalLink className="w-3 h-3 inline ml-1.5 text-white/30" />
                            )}
                          </h3>
                        </a>
                        <div className="flex items-center gap-2 text-xs">
                          <span className={cn("font-medium", getCredibilityColor(article.source_credibility?.score))}>
                            {article.source.name}
                          </span>
                          <span className="text-white/20">•</span>
                          <Clock className="w-3 h-3 text-white/20" />
                          <span className="text-white/20">
                            {formatDistanceToNow(new Date(article.publishedAt), { addSuffix: true })}
                          </span>
                        </div>
                      </div>

                      {/* Indicator badges */}
                      {article.indicator_relevance && article.indicator_relevance.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {article.indicator_relevance.slice(0, 3).map((indicatorId, i) => (
                            <Badge 
                              key={i} 
                              variant={getIndicatorStatus(indicatorId) as any}
                              size="sm"
                            >
                              {indicatorId.replace(/_/g, ' ').toUpperCase()}
                            </Badge>
                          ))}
                          {article.indicator_relevance.length > 3 && (
                            <Badge variant="default" size="sm">
                              +{article.indicator_relevance.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}

                      {/* Relationship text */}
                      <p className="text-xs text-white/30 mb-2">
                        <Shield className="w-3 h-3 inline mr-1" />
                        {getIndicatorRelationshipText(article.indicator_relevance)}
                      </p>

                      {/* Expanded content */}
                      <AnimatePresence>
                        {expandedArticle === index && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="pt-2 mt-2 border-t border-white/[0.08]">
                              <p className="text-xs text-white/50 mb-3 line-clamp-3">
                                {article.description}
                              </p>
                              {article.url !== '#' && (
                                <a
                                  href={article.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  Read full article
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Hover indicator */}
                      <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                        <ChevronRight className="w-3 h-3 text-white/20" />
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>

          {/* Footer with stats */}
          <div className="p-4 border-t border-white/[0.04] bg-white/[0.03]">
            <div className="flex items-center justify-between text-xs text-white/20">
              <span>{articles.length} articles</span>
              <span>Auto-refresh enabled</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};