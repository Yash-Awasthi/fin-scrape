import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Radio, 
  AlertTriangle, 
  TrendingUp, 
  ExternalLink,
  Pause,
  Play
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { newsIntelligence } from '../../services/newsIntelligence';

interface NewsTickerItem {
  title: string;
  url: string;
  source: string;
  urgency: 'low' | 'medium' | 'high';
  indicator?: string;
}

interface NewsTickerProps {
  className?: string;
  showControls?: boolean;
  maxItems?: number;
  autoRotate?: boolean;
  rotationInterval?: number;
}

export const NewsTicker: React.FC<NewsTickerProps> = ({
  className,
  showControls = true,
  maxItems = 5,
  autoRotate = true,
  rotationInterval = 8000
}) => {
  const [items, setItems] = useState<NewsTickerItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoRotate);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTickerItems();
  }, [maxItems]);

  useEffect(() => {
    if (isPlaying && items.length > 1) {
      const interval = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % items.length);
      }, rotationInterval);
      
      return () => clearInterval(interval);
    }
  }, [isPlaying, items.length, rotationInterval]);

  const loadTickerItems = async () => {
    try {
      setLoading(true);
      const news = await newsIntelligence.getGlobalNewsFeed(maxItems);
      
      const tickerItems: NewsTickerItem[] = news.map(article => ({
        title: article.title,
        url: article.url,
        source: article.source.name,
        urgency: determineUrgency(article),
        indicator: article.indicator_relevance?.[0]
      }));
      
      setItems(tickerItems);
    } catch (error) {
      console.error('Failed to load ticker items:', error);
      // Use fallback items
      setItems(getFallbackItems());
    } finally {
      setLoading(false);
    }
  };

  const determineUrgency = (article: any): 'low' | 'medium' | 'high' => {
    const title = article.title.toLowerCase();
    const relevanceScore = article.relevance_score || 0;
    
    // High urgency keywords
    if (title.includes('crisis') || title.includes('emergency') || 
        title.includes('breaking') || title.includes('urgent') ||
        title.includes('alert') || relevanceScore >= 9) {
      return 'high';
    }
    
    // Medium urgency keywords
    if (title.includes('warning') || title.includes('concern') ||
        title.includes('risk') || title.includes('threat') ||
        relevanceScore >= 6) {
      return 'medium';
    }
    
    return 'low';
  };

  const getFallbackItems = (): NewsTickerItem[] => [
    {
      title: "Federal Reserve signals cautious approach to interest rate policy amid economic uncertainty",
      url: "https://news.google.com/search?q=federal+reserve+interest+rates",
      source: "Wall Street Journal",
      urgency: 'medium',
      indicator: 'econ_01_treasury_tail'
    },
    {
      title: "Market volatility increases as investors weigh geopolitical tensions",
      url: "https://news.google.com/search?q=market+volatility+treasury+yields",
      source: "Bloomberg",
      urgency: 'medium',
      indicator: 'market_01_intraday_swing'
    },
    {
      title: "Global supply chain monitoring shows resilient systems despite regional conflicts",
      url: "https://news.google.com/search?q=global+supply+chain+conflicts",
      source: "Reuters",
      urgency: 'low',
      indicator: 'global_conflict_intensity'
    }
  ];

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'medium':
        return <TrendingUp className="w-4 h-4 text-amber-400" />;
      default:
        return <Radio className="w-4 h-4 text-green-400" />;
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return 'border-red-500/30 bg-red-500/5';
      case 'medium':
        return 'border-amber-500/30 bg-amber-500/5';
      default:
        return 'border-green-500/30 bg-green-500/5';
    }
  };

  if (loading) {
    return (
      <div className={cn("bg-white/[0.03] border border-white/[0.04] rounded-lg p-3", className)}>
        <div className="flex items-center gap-3">
          <Radio className="w-4 h-4 text-white/30 animate-pulse" />
          <div className="flex-1">
            <div className="h-4 bg-white/10 rounded animate-pulse w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return null;
  }

  const currentItem = items[currentIndex];

  return (
    <motion.div
      className={cn(
        "bg-white/[0.03] border rounded-lg p-3 transition-all duration-300",
        getUrgencyColor(currentItem.urgency),
        className
      )}
      key={currentIndex}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 flex-shrink-0">
          {getUrgencyIcon(currentItem.urgency)}
          <span className="text-xs font-medium text-white/30 uppercase tracking-wide">
            {currentItem.source}
          </span>
        </div>
        
        <div className="flex-1 min-w-0">
          <motion.p
            className="text-sm text-white truncate cursor-pointer hover:text-white/50 transition-colors"
            onClick={() => currentItem.url !== '#' && window.open(currentItem.url, '_blank')}
            title={currentItem.title}
            key={currentItem.title}
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.4 }}
          >
            {currentItem.title}
          </motion.p>
          
          {currentItem.indicator && (
            <div className="mt-1">
              <span className="text-xs text-white/20">
                Relates to: {currentItem.indicator.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {showControls && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {items.length > 1 && (
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-1 text-white/30 hover:text-white transition-colors"
                title={isPlaying ? 'Pause ticker' : 'Resume ticker'}
              >
                {isPlaying ? (
                  <Pause className="w-3 h-3" />
                ) : (
                  <Play className="w-3 h-3" />
                )}
              </button>
            )}
            
            {currentItem.url !== '#' && (
              <a
                href={currentItem.url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1 text-white/30 hover:text-white transition-colors"
                title="Read full article"
              >
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        )}
      </div>

      {items.length > 1 && (
        <div className="flex items-center gap-1 mt-2">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={cn(
                "w-2 h-1 rounded-full transition-all",
                index === currentIndex 
                  ? "bg-white" 
                  : "bg-white/15 hover:bg-white/20"
              )}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
};