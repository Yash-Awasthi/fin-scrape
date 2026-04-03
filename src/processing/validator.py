import re
import math
from src.processing.constants import *

def calculate_heuristic_score(text, event_type):
    """
    Calculates a secondary 'heuristic' score based on keywords.
    Returns: (sentiment_label, impact_score)
    """
    text_lower = text.lower()
    
    # Sentiment calculation
    sp = len([w for w in POSITIVE_STRONG if w in text_lower])
    wp = len([w for w in POSITIVE_WEAK if w in text_lower])
    sn = len([w for w in NEGATIVE_STRONG if text_lower.count(w)])
    wn = len([w for w in NEGATIVE_WEAK if text_lower.count(w)])
    
    raw_sentiment = (2 * sp + wp) - (2 * sn + wn)
    
    if raw_sentiment >= 2:
        sentiment = "positive"
    elif raw_sentiment <= -2:
        sentiment = "negative"
    else:
        sentiment = "neutral"
        
    # Impact calculation (Logistic weight)
    base_impact = EVENT_BASE_IMPACT.get(event_type, 0.3)
    
    # Magnitude boost
    mag_boost = len([w for w in MAGNITUDE_WORDS if w in text_lower]) * 0.1
    
    # Dollar boost
    dollar_boost = 0
    if re.search(r'\$\d+\s*(?:billion|b|bn)', text_lower):
        dollar_boost = 0.3
    elif re.search(r'\$\d+\s*(?:million|m|mn)', text_lower):
        dollar_boost = 0.1
        
    # Logistic squashing
    logit_base = math.log(base_impact / (1.0 - base_impact + 1e-9))
    total_log = math.log(base_impact) + mag_boost + dollar_boost
    
    heuristic_impact = 1.0 / (1.0 + math.exp(-(total_log + logit_base)))
    
    return sentiment, round(heuristic_impact, 2)

def check_divergence(ai_sentiment, heuristic_sentiment):
    """
    Flags if AI and Heuristics disagree on polarity.
    """
    if ai_sentiment == "neutral" or heuristic_sentiment == "neutral":
        return False
    return ai_sentiment != heuristic_sentiment

def clean_tickers(tickers):
    """
    Remove noise tickers like 'ON', 'IT', 'AI' using the stopword list.
    """
    return [t for t in tickers if t.upper() not in TICKER_STOPWORDS]
