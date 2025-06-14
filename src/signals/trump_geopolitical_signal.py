"""
Trump Geopolitical Signal - Defense Stock Impact from Political Statements
Analyzes Trump statements and geopolitical rhetoric affecting defense spending
"""
import yfinance as yf
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_signal import BaseSignal

class TrumpGeopoliticalSignal(BaseSignal):
    """
    Trump Geopolitical Signal for Defense Stock Trading
    
    Monitors political statements and rhetoric that affect defense spending:
    - NATO/alliance comments affecting defense budgets
    - Military strength/weakness discussions
    - Geopolitical tension escalation/de-escalation
    - Defense budget and spending commentary
    - "Peace through strength" vs isolationist messaging
    
    Note: Since Truth Social doesn't have public API, we monitor financial
    news that reports on politically-relevant statements affecting defense sector.
    
    Strategy:
    - Pro-defense spending rhetoric: BUY (sector tailwind)
    - Military strength emphasis: BUY (defense priority)
    - Isolationist/budget cutting: SELL (sector headwind)
    - Geopolitical tension escalation: BUY (defense demand)
    """
    
    def __init__(self):
        super().__init__("trump_geopolitical")
        self.signal_name = "trump_geopolitical"
        
        # Keywords indicating pro-defense stance
        self.pro_defense_keywords = [
            "peace through strength", "rebuild military", "strengthen defense",
            "military superiority", "defense spending", "modernize military",
            "deterrence", "strong military", "military readiness",
            "national security", "defend america", "military technology"
        ]
        
        # Keywords indicating isolationist/budget cutting stance  
        self.anti_defense_keywords = [
            "endless wars", "bring troops home", "reduce military",
            "cut defense", "military industrial", "wasteful spending",
            "america first" + "isolat", "withdraw", "reduce overseas"
        ]
        
        # Geopolitical tension keywords
        self.tension_keywords = [
            "china threat", "chinese military", "taiwan", "south china sea",
            "russia", "putin", "ukraine", "nato article", "iran threat",
            "middle east", "nuclear", "missile threat", "cyber warfare"
        ]
        
        # Alliance/NATO keywords
        self.alliance_keywords = [
            "nato", "allies", "alliance", "burden sharing", "2% spending",
            "defense commitment", "collective defense", "treaty",
            "partnership", "coalition", "mutual defense"
        ]
        
        # Trump-related keywords for relevance filtering
        self.trump_keywords = [
            "trump", "donald trump", "president trump", "former president",
            "truth social", "mar-a-lago", "campaign", "republican"
        ]
    
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze Trump/political statements affecting defense sector"""
        try:
            # Get political/financial news mentioning Trump and defense
            relevant_news = self._get_trump_defense_news()
            
            if not relevant_news:
                return self._create_neutral_signal("No recent Trump defense-related news")
            
            # Analyze sentiment and defense impact
            defense_impact_score = self._analyze_defense_impact(relevant_news)
            geopolitical_score = self._analyze_geopolitical_impact(relevant_news)
            
            # Combine scores
            combined_score = (defense_impact_score * 0.6) + (geopolitical_score * 0.4)
            
            # Generate signal
            direction, confidence, reasoning = self._generate_geopolitical_signal(
                combined_score, defense_impact_score, geopolitical_score, relevant_news
            )
            
            return {
                'signal': self.signal_name,
                'direction': direction,
                'confidence': confidence,
                'strength': min(confidence / 100.0, 1.0),
                'reasoning': reasoning,
                'metadata': {
                    'news_count': len(relevant_news),
                    'defense_impact_score': round(defense_impact_score, 2),
                    'geopolitical_score': round(geopolitical_score, 2),
                    'combined_score': round(combined_score, 2),
                    'key_themes': self._extract_key_themes(relevant_news),
                    'recency_hours': self._get_most_recent_hours(relevant_news)
                }
            }
            
        except Exception as e:
            return self._create_error_signal(f"Trump geopolitical analysis failed: {str(e)}")
    
    def _get_trump_defense_news(self) -> List[Dict]:
        """Get news mentioning Trump and defense-related topics"""
        try:
            # Search political/financial news for Trump + defense keywords
            # Since we can't access Truth Social directly, we look for financial news
            # that reports on Trump statements affecting defense sector
            
            relevant_news = []
            
            # Check defense sector news sources (using major defense stock news as proxy)
            defense_sources = ['RTX', 'LMT', 'NOC', 'GD']
            
            for ticker in defense_sources:
                try:
                    stock = yf.Ticker(ticker)
                    news = stock.news
                    
                    # Filter for Trump-related defense news
                    cutoff_date = datetime.now() - timedelta(days=5)  # More recent for political news
                    
                    for article in news[:8]:  # Check recent articles
                        try:
                            pub_date = datetime.fromtimestamp(article.get('providerPublishTime', 0))
                            if pub_date > cutoff_date:
                                title = article.get('title', '').lower()
                                summary = article.get('summary', '').lower()
                                text = title + ' ' + summary
                                
                                # Check if mentions Trump AND defense/political themes
                                has_trump = any(keyword in text for keyword in self.trump_keywords)
                                has_defense_theme = (
                                    any(keyword in text for keyword in self.pro_defense_keywords) or
                                    any(keyword in text for keyword in self.anti_defense_keywords) or
                                    any(keyword in text for keyword in self.tension_keywords) or
                                    any(keyword in text for keyword in self.alliance_keywords)
                                )
                                
                                if has_trump and has_defense_theme:
                                    relevant_news.append({
                                        'title': article.get('title', ''),
                                        'summary': article.get('summary', ''),
                                        'date': pub_date,
                                        'source_ticker': ticker,
                                        'url': article.get('link', '')
                                    })
                        except:
                            continue
                except:
                    continue
            
            # Also check broader political/financial news
            # (In production, you'd use dedicated political news APIs)
            
            return relevant_news
            
        except Exception:
            return []
    
    def _analyze_defense_impact(self, news_articles: List[Dict]) -> float:
        """Analyze impact on defense spending/sector from Trump statements"""
        if not news_articles:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for article in news_articles:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            text = title + ' ' + summary
            
            # Calculate relevance weight
            weight = self._calculate_defense_relevance(text)
            if weight == 0:
                continue
            
            # Calculate defense impact score
            impact = self._calculate_defense_sentiment(text)
            
            total_score += impact * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _analyze_geopolitical_impact(self, news_articles: List[Dict]) -> float:
        """Analyze geopolitical tension impact from statements"""
        if not news_articles:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for article in news_articles:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            text = title + ' ' + summary
            
            # Calculate geopolitical relevance
            weight = self._calculate_geopolitical_relevance(text)
            if weight == 0:
                continue
            
            # Calculate tension impact (higher tension = more defense demand)
            tension_impact = self._calculate_tension_impact(text)
            
            total_score += tension_impact * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_defense_relevance(self, text: str) -> float:
        """Calculate how relevant text is to defense spending"""
        weight = 0.0
        
        # Pro-defense keywords
        pro_count = sum(1 for keyword in self.pro_defense_keywords if keyword in text)
        weight += pro_count * 1.5
        
        # Anti-defense keywords  
        anti_count = sum(1 for keyword in self.anti_defense_keywords if keyword in text)
        weight += anti_count * 1.5
        
        # Alliance/NATO mentions
        alliance_count = sum(1 for keyword in self.alliance_keywords if keyword in text)
        weight += alliance_count * 1.0
        
        return min(weight, 5.0)
    
    def _calculate_defense_sentiment(self, text: str) -> float:
        """Calculate defense spending sentiment from -1 to +1"""
        pro_score = sum(1 for keyword in self.pro_defense_keywords if keyword in text)
        anti_score = sum(1 for keyword in self.anti_defense_keywords if keyword in text)
        
        net_score = pro_score - anti_score
        return max(-1.0, min(1.0, net_score / 2.0))
    
    def _calculate_geopolitical_relevance(self, text: str) -> float:
        """Calculate geopolitical relevance weight"""
        tension_count = sum(1 for keyword in self.tension_keywords if keyword in text)
        return min(tension_count * 1.0, 3.0)
    
    def _calculate_tension_impact(self, text: str) -> float:
        """Calculate geopolitical tension impact (higher = more defense demand)"""
        # Keywords that suggest escalation (positive for defense)
        escalation_words = ["threat", "aggression", "conflict", "war", "nuclear", "invasion"]
        # Keywords that suggest de-escalation (negative for defense)
        deescalation_words = ["peace", "diplomacy", "agreement", "resolution", "withdraw"]
        
        escalation_score = sum(1 for word in escalation_words if word in text)
        deescalation_score = sum(1 for word in deescalation_words if word in text)
        
        net_score = escalation_score - deescalation_score
        return max(-1.0, min(1.0, net_score / 2.0))
    
    def _generate_geopolitical_signal(self, combined_score: float, defense_score: float,
                                    geo_score: float, news: List) -> tuple:
        """Generate trading signal based on geopolitical analysis"""
        
        # No relevant news
        if len(news) == 0:
            return "HOLD", 50, "No recent Trump defense-related news"
        
        # Strong positive for defense
        if combined_score > 1.0:
            confidence = 85
            return "BUY", confidence, f"Strong pro-defense political sentiment (score: {combined_score:.1f})"
        
        # Moderate positive
        elif combined_score > 0.3:
            confidence = 70
            return "BUY", confidence, f"Pro-defense political sentiment (score: {combined_score:.1f})"
        
        # Neutral to slightly positive
        elif combined_score > -0.1:
            confidence = 55
            return "HOLD", confidence, f"Neutral political sentiment (score: {combined_score:.1f})"
        
        # Moderate negative
        elif combined_score > -0.5:
            confidence = 70
            return "SELL", confidence, f"Anti-defense political sentiment (score: {combined_score:.1f})"
        
        # Strong negative
        else:
            confidence = 85
            return "SELL", confidence, f"Strong anti-defense political sentiment (score: {combined_score:.1f})"
    
    def _extract_key_themes(self, news_articles: List[Dict]) -> List[str]:
        """Extract key themes from relevant news"""
        themes = []
        
        for article in news_articles[:3]:
            title = article.get('title', '')
            if title:
                # Extract key phrases (simplified)
                if any(word in title.lower() for word in ['nato', 'alliance']):
                    themes.append("NATO/Alliance")
                if any(word in title.lower() for word in ['china', 'taiwan']):
                    themes.append("China Tensions")
                if any(word in title.lower() for word in ['russia', 'ukraine']):
                    themes.append("Russia/Ukraine")
                if any(word in title.lower() for word in ['defense', 'military']):
                    themes.append("Defense Policy")
        
        return list(set(themes))
    
    def _get_most_recent_hours(self, news_articles: List[Dict]) -> int:
        """Get hours since most recent relevant news"""
        if not news_articles:
            return 999
        
        most_recent = max(article.get('date', datetime.min) for article in news_articles)
        hours_ago = (datetime.now() - most_recent).total_seconds() / 3600
        return int(hours_ago)
    
    def _create_neutral_signal(self, reason: str) -> Dict:
        """Create a neutral signal"""
        return {
            'signal': self.signal_name,
            'direction': 'HOLD',
            'confidence': 50,
            'strength': 0.5,
            'reasoning': reason,
            'metadata': {
                'news_count': 0,
                'key_themes': [],
                'recency_hours': 999
            }
        }
    
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
        """Simple backtest implementation for Trump geopolitical signal"""
        return {
            'signal_name': self.signal_name,
            'backtest_period': f"{start_date} to {end_date}",
            'note': 'Trump geopolitical signal backtest requires historical political news data',
            'estimated_performance': 'Variable based on political climate and defense messaging'
        }