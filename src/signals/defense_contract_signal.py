"""
Defense Contract News Signal - RTX-Specific Catalyst Detection
Analyzes defense contract awards, geopolitical events, and DoD spending news
"""
import yfinance as yf
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_signal import BaseSignal

class DefenseContractSignal(BaseSignal):
    """
    Defense Contract News Signal for RTX Trading
    
    Monitors:
    - DoD contract awards mentioning RTX/Raytheon
    - Defense budget news and appropriations
    - Geopolitical events affecting defense spending
    - NATO/ally defense procurement news
    - Military technology development announcements
    
    Strategy:
    - Positive contract news: BUY (immediate catalyst)
    - Budget increase news: BUY (sector tailwind)
    - Geopolitical tensions: BUY (defense spending driver)
    - Budget cuts/delays: SELL (sector headwind)
    """
    
    def __init__(self):
        super().__init__("defense_contract")
        self.signal_name = "defense_contract"
        
        # Keywords for defense contract detection
        self.rtx_keywords = [
            "raytheon", "rtx", "rtx corporation", "raytheon technologies",
            "pratt & whitney", "collins aerospace", "raytheon missiles"
        ]
        
        self.contract_keywords = [
            "contract", "award", "awarded", "procurement", "purchase",
            "billion", "million", "dod", "pentagon", "air force", "navy",
            "army", "defense", "military", "missile", "aircraft", "engine"
        ]
        
        self.positive_keywords = [
            "awarded", "wins", "selected", "increase", "boost", "expand",
            "additional", "extension", "renewal", "upgrade", "modernization"
        ]
        
        self.negative_keywords = [
            "cut", "reduce", "delay", "cancel", "lose", "lost", "decline",
            "decrease", "budget reduction", "sequestration"
        ]
        
        self.geopolitical_keywords = [
            "ukraine", "russia", "china", "taiwan", "nato", "iran",
            "middle east", "conflict", "tension", "threat", "sanctions"
        ]
    
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze defense contract and geopolitical news affecting RTX"""
        try:
            # Get RTX-specific news
            rtx_news = self._get_rtx_news()
            
            # Get broader defense industry news
            defense_news = self._get_defense_industry_news()
            
            # Analyze news sentiment and relevance
            rtx_score = self._analyze_news_sentiment(rtx_news, is_rtx_specific=True)
            defense_score = self._analyze_news_sentiment(defense_news, is_rtx_specific=False)
            
            # Combine scores (RTX-specific weighted higher)
            combined_score = (rtx_score * 0.7) + (defense_score * 0.3)
            
            # Generate signal
            direction, confidence, reasoning = self._generate_contract_signal(
                combined_score, rtx_score, defense_score, rtx_news, defense_news
            )
            
            return {
                'signal': self.signal_name,
                'direction': direction,
                'confidence': confidence,
                'strength': min(confidence / 100.0, 1.0),
                'reasoning': reasoning,
                'metadata': {
                    'rtx_news_count': len(rtx_news),
                    'defense_news_count': len(defense_news),
                    'rtx_sentiment_score': round(rtx_score, 2),
                    'defense_sentiment_score': round(defense_score, 2),
                    'combined_score': round(combined_score, 2),
                    'key_stories': self._extract_key_stories(rtx_news, defense_news)
                }
            }
            
        except Exception as e:
            return self._create_error_signal(f"Defense contract analysis failed: {str(e)}")
    
    def _get_rtx_news(self) -> List[Dict]:
        """Get RTX-specific news from financial sources"""
        try:
            rtx = yf.Ticker("RTX")
            news = rtx.news
            
            # Filter for recent news (last 7 days)
            recent_news = []
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for article in news[:10]:  # Check latest 10 articles
                try:
                    pub_date = datetime.fromtimestamp(article.get('providerPublishTime', 0))
                    if pub_date > cutoff_date:
                        recent_news.append({
                            'title': article.get('title', ''),
                            'summary': article.get('summary', ''),
                            'date': pub_date,
                            'url': article.get('link', '')
                        })
                except:
                    continue
            
            return recent_news
            
        except Exception:
            return []
    
    def _get_defense_industry_news(self) -> List[Dict]:
        """Get broader defense industry news (simplified version)"""
        try:
            # In a production system, you'd use news APIs like:
            # - Defense News RSS feeds
            # - DoD contract announcement feeds  
            # - Reuters/Bloomberg defense sector feeds
            
            # For now, we'll use a simplified approach with defense sector ETF news
            # as a proxy for industry sentiment
            
            defense_tickers = ['LMT', 'NOC', 'GD', 'BA']  # Major defense contractors
            defense_news = []
            
            for ticker in defense_tickers:
                try:
                    stock = yf.Ticker(ticker)
                    news = stock.news
                    
                    # Get recent news
                    cutoff_date = datetime.now() - timedelta(days=7)
                    for article in news[:5]:  # Limit to avoid rate limits
                        try:
                            pub_date = datetime.fromtimestamp(article.get('providerPublishTime', 0))
                            if pub_date > cutoff_date:
                                title = article.get('title', '')
                                summary = article.get('summary', '')
                                
                                # Only include if it mentions defense/military/contract keywords
                                text = (title + ' ' + summary).lower()
                                if any(keyword in text for keyword in self.contract_keywords):
                                    defense_news.append({
                                        'title': title,
                                        'summary': summary,
                                        'date': pub_date,
                                        'ticker': ticker,
                                        'url': article.get('link', '')
                                    })
                        except:
                            continue
                except:
                    continue
            
            return defense_news
            
        except Exception:
            return []
    
    def _analyze_news_sentiment(self, news_articles: List[Dict], is_rtx_specific: bool) -> float:
        """Analyze sentiment of news articles for defense contract impact"""
        if not news_articles:
            return 0.0  # Neutral
        
        total_score = 0.0
        total_weight = 0.0
        
        for article in news_articles:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            text = title + ' ' + summary
            
            # Calculate relevance weight
            weight = self._calculate_relevance_weight(text, is_rtx_specific)
            if weight == 0:
                continue
            
            # Calculate sentiment score
            sentiment = self._calculate_sentiment_score(text)
            
            total_score += sentiment * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return total_score / total_weight
    
    def _calculate_relevance_weight(self, text: str, is_rtx_specific: bool) -> float:
        """Calculate how relevant an article is to RTX/defense contracts"""
        weight = 0.0
        
        # RTX-specific mentions (highest weight)
        if is_rtx_specific:
            rtx_mentions = sum(1 for keyword in self.rtx_keywords if keyword in text)
            weight += rtx_mentions * 2.0
        
        # Contract/procurement mentions
        contract_mentions = sum(1 for keyword in self.contract_keywords if keyword in text)
        weight += contract_mentions * 1.0
        
        # Geopolitical relevance
        geo_mentions = sum(1 for keyword in self.geopolitical_keywords if keyword in text)
        weight += geo_mentions * 0.5
        
        # Money mentions (contract values)
        if any(term in text for term in ['billion', 'million', '$']):
            weight += 1.0
        
        return min(weight, 5.0)  # Cap at 5.0
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score from -1 (negative) to +1 (positive)"""
        positive_score = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_score = sum(1 for keyword in self.negative_keywords if keyword in text)
        
        # Normalize to -1 to +1 range
        net_score = positive_score - negative_score
        
        if net_score > 0:
            return min(net_score / 3.0, 1.0)  # Positive sentiment
        elif net_score < 0:
            return max(net_score / 3.0, -1.0)  # Negative sentiment
        else:
            return 0.0  # Neutral
    
    def _generate_contract_signal(self, combined_score: float, rtx_score: float, 
                                defense_score: float, rtx_news: List, defense_news: List) -> tuple:
        """Generate trading signal based on defense contract sentiment"""
        
        # No relevant news
        if len(rtx_news) == 0 and len(defense_news) == 0:
            return "HOLD", 50, "No recent defense contract news"
        
        # Strong positive sentiment
        if combined_score > 1.5:
            confidence = 90
            return "BUY", confidence, f"Strong positive defense news (score: {combined_score:.1f})"
        
        # Moderate positive sentiment
        elif combined_score > 0.5:
            confidence = 75
            return "BUY", confidence, f"Positive defense news (score: {combined_score:.1f})"
        
        # Slight positive sentiment
        elif combined_score > 0.1:
            confidence = 65
            return "BUY", confidence, f"Mildly positive defense news (score: {combined_score:.1f})"
        
        # Neutral sentiment
        elif combined_score > -0.1:
            confidence = 50
            return "HOLD", confidence, f"Neutral defense news (score: {combined_score:.1f})"
        
        # Slight negative sentiment
        elif combined_score > -0.5:
            confidence = 65
            return "SELL", confidence, f"Mildly negative defense news (score: {combined_score:.1f})"
        
        # Moderate negative sentiment
        elif combined_score > -1.5:
            confidence = 75
            return "SELL", confidence, f"Negative defense news (score: {combined_score:.1f})"
        
        # Strong negative sentiment
        else:
            confidence = 90
            return "SELL", confidence, f"Strong negative defense news (score: {combined_score:.1f})"
    
    def _extract_key_stories(self, rtx_news: List, defense_news: List) -> List[str]:
        """Extract key story headlines for metadata"""
        key_stories = []
        
        # Add RTX-specific stories (up to 3)
        for article in rtx_news[:3]:
            title = article.get('title', '')
            if title and len(title) > 10:
                key_stories.append(f"RTX: {title[:100]}...")
        
        # Add defense industry stories (up to 2)
        for article in defense_news[:2]:
            title = article.get('title', '')
            ticker = article.get('ticker', 'DEF')
            if title and len(title) > 10:
                key_stories.append(f"{ticker}: {title[:100]}...")
        
        return key_stories
    
    def _create_error_signal(self, error_msg: str) -> Dict:
        """Create an error signal"""
        return {
            'signal': self.signal_name,
            'direction': 'HOLD',
            'confidence': 50,
            'strength': 0.5,
            'reasoning': f"Error: {error_msg}",
            'metadata': {
                'error': True,
                'error_message': error_msg
            }
        }
    
    async def backtest(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """Simple backtest implementation for defense contract signal"""
        return {
            'signal_name': self.signal_name,
            'backtest_period': f"{start_date} to {end_date}",
            'note': 'Defense contract signal backtest requires historical news data',
            'estimated_performance': 'Positive correlation with defense sector events'
        }