"""
News Sentiment Analysis Signal
AI-powered analysis of RTX and defense sector news
"""
import openai
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
from loguru import logger

from config.trading_config import config

class NewsSentimentSignal:
    """Analyze news sentiment for RTX and defense sector"""
    
    def __init__(self):
        self.signal_name = "news_sentiment"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.15)
        self.news_cache = {}
        self.last_analysis = None
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze news sentiment for trading signals"""
        
        try:
            # Get recent news
            news_data = await self._get_rtx_news(symbol)
            
            if not news_data:
                return self._create_neutral_signal("No recent news found")
            
            # Analyze sentiment with AI
            sentiment_analysis = await self._analyze_sentiment_with_ai(news_data)
            
            # Generate signal
            signal = self._generate_signal(sentiment_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📰 News sentiment error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_rtx_news(self, symbol: str) -> List[Dict]:
        """Get recent RTX-related news"""
        try:
            # Use yfinance for news (free and reliable)
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            # Filter recent news (last 24 hours)
            recent_news = []
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for article in news[:10]:  # Top 10 articles
                publish_time = datetime.fromtimestamp(article.get('providerPublishTime', 0))
                
                if publish_time > cutoff_time:
                    recent_news.append({
                        'title': article.get('title', ''),
                        'summary': article.get('summary', ''),
                        'publisher': article.get('publisher', ''),
                        'publish_time': publish_time.isoformat(),
                        'url': article.get('link', '')
                    })
            
            logger.info(f"📰 Found {len(recent_news)} recent {symbol} articles")
            return recent_news
            
        except Exception as e:
            logger.error(f"📰 News retrieval error: {e}")
            return []
    
    async def _analyze_sentiment_with_ai(self, news_data: List[Dict]) -> Dict:
        """Analyze news sentiment using OpenAI"""
        
        if not news_data:
            return {"sentiment": "neutral", "confidence": 0.5, "reasoning": "No news to analyze"}
        
        # Prepare news text for analysis
        news_text = "\n\n".join([
            f"Title: {article['title']}\nSummary: {article.get('summary', 'No summary')}"
            for article in news_data[:5]  # Analyze top 5 articles
        ])
        
        try:
            # Use OpenAI for sentiment analysis
            import openai
            import os
            
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""
            You are a professional financial analyst. Analyze the following RTX Corporation news for trading sentiment.
            
            NEWS ARTICLES:
            {news_text}
            
            Provide analysis in this JSON format:
            {{
                "sentiment": "bullish|bearish|neutral",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation",
                "key_factors": ["factor1", "factor2"],
                "time_horizon": "short|medium|long"
            }}
            
            Focus on:
            - Defense spending trends
            - Contract wins/losses
            - Geopolitical factors
            - Company performance
            - Market conditions
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
            )
            
            # Parse AI response
            ai_analysis = response.choices[0].message.content
            
            # Extract sentiment data (simplified parsing)
            if "bullish" in ai_analysis.lower():
                sentiment = "bullish"
                confidence = 0.7
            elif "bearish" in ai_analysis.lower():
                sentiment = "bearish"
                confidence = 0.7
            else:
                sentiment = "neutral"
                confidence = 0.5
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "reasoning": ai_analysis[:200] + "..." if len(ai_analysis) > 200 else ai_analysis,
                "articles_analyzed": len(news_data),
                "ai_response": ai_analysis
            }
            
        except Exception as e:
            logger.error(f"🤖 AI sentiment analysis error: {e}")
            
            # Fallback: Simple keyword analysis
            return await self._simple_sentiment_analysis(news_data)
    
    async def _simple_sentiment_analysis(self, news_data: List[Dict]) -> Dict:
        """Fallback sentiment analysis using keywords"""
        
        positive_keywords = [
            "contract", "award", "win", "revenue", "growth", "profit",
            "defense", "military", "partnership", "expansion", "innovation"
        ]
        
        negative_keywords = [
            "loss", "cut", "layoff", "decline", "issue", "problem",
            "lawsuit", "fine", "investigation", "concern", "risk"
        ]
        
        positive_score = 0
        negative_score = 0
        
        for article in news_data:
            text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
            
            positive_score += sum(1 for keyword in positive_keywords if keyword in text)
            negative_score += sum(1 for keyword in negative_keywords if keyword in text)
        
        # Determine sentiment
        if positive_score > negative_score + 1:
            sentiment = "bullish"
            confidence = min(0.8, 0.5 + (positive_score - negative_score) * 0.1)
        elif negative_score > positive_score + 1:
            sentiment = "bearish"
            confidence = min(0.8, 0.5 + (negative_score - positive_score) * 0.1)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": f"Keyword analysis: {positive_score} positive, {negative_score} negative signals",
            "method": "keyword_fallback"
        }
    
    def _generate_signal(self, sentiment_analysis: Dict) -> Dict:
        """Generate trading signal from sentiment analysis"""
        
        sentiment = sentiment_analysis.get("sentiment", "neutral")
        confidence = sentiment_analysis.get("confidence", 0.5)
        
        # Convert sentiment to trading signal
        if sentiment == "bullish" and confidence > 0.6:
            direction = "BUY"
            signal_strength = confidence * self.weight
        elif sentiment == "bearish" and confidence > 0.6:
            direction = "SELL"
            signal_strength = confidence * self.weight
        else:
            direction = "HOLD"
            signal_strength = 0.1
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": sentiment_analysis.get("reasoning", "Sentiment analysis"),
            "timestamp": datetime.now().isoformat(),
            "raw_data": sentiment_analysis
        }
    
    def _create_neutral_signal(self, reason: str) -> Dict:
        """Create neutral signal with reason"""
        return {
            "signal_name": self.signal_name,
            "direction": "HOLD",
            "strength": 0.1,
            "confidence": 0.5,
            "reasoning": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_signal_status(self) -> Dict:
        """Get current signal status"""
        return {
            "signal_name": self.signal_name,
            "weight": self.weight,
            "last_analysis": self.last_analysis,
            "status": "operational"
        } 