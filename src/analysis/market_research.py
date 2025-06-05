"""
Real Market Price Analysis for $1000 Budget Strategy
Check current prices and realistic options strategies
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

class MarketResearch:
    """Research current market prices for realistic strategy design"""
    
    def __init__(self):
        self.budget = 1000
        self.commission_per_contract = 0.65  # IBKR Lite
        
    async def analyze_current_prices(self):
        """Get current market prices for strategy planning"""
        
        logger.info("🔍 Analyzing current market prices for $1000 budget...")
        
        # Assets to analyze
        symbols = {
            'RTX': 'Raytheon Technologies',
            'IWM': 'Russell 2000 ETF', 
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ ETF',
            'TLT': 'Treasury Bond ETF',
            'XLF': 'Financial Sector ETF',
            'SQQQ': '3x Inverse NASDAQ',  # Cheaper options
            'TQQQ': '3x NASDAQ',         # Cheaper options
        }
        
        results = {}
        
        for symbol, name in symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                
                # Get current price
                hist = ticker.history(period="5d")
                if hist.empty:
                    continue
                    
                current_price = hist['Close'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                
                # Calculate volatility
                returns = hist['Close'].pct_change()
                volatility = returns.std() * np.sqrt(252)  # Annualized
                
                # Get basic info
                info = ticker.info
                market_cap = info.get('marketCap', 0)
                
                results[symbol] = {
                    'name': name,
                    'current_price': round(current_price, 2),
                    'volume': volume,
                    'volatility': round(volatility, 3),
                    'market_cap': market_cap,
                    'affordable_shares': int(self.budget / current_price),
                    'per_share_budget': round(self.budget / current_price, 2)
                }
                
                logger.info(f"{symbol}: ${current_price:.2f} - Can afford {int(self.budget / current_price)} shares")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        return results
    
    async def analyze_options_strategies(self):
        """Analyze realistic options strategies for $1000"""
        
        logger.info("📊 Analyzing realistic options strategies...")
        
        strategies = {
            'long_calls_iwm': {
                'description': 'Buy IWM calls (bullish)',
                'typical_cost': 150,  # $1.50 per contract
                'max_positions': int((self.budget - 100) / 150),  # Keep $100 buffer
                'profit_potential': '50-200%',
                'success_rate': '25-35%',
                'timeframe': '2-6 weeks'
            },
            
            'long_puts_iwm': {
                'description': 'Buy IWM puts (bearish)', 
                'typical_cost': 150,
                'max_positions': int((self.budget - 100) / 150),
                'profit_potential': '50-300%',
                'success_rate': '25-35%',
                'timeframe': '2-6 weeks'
            },
            
            'long_calls_sqqq': {
                'description': 'Buy SQQQ calls (market crash bet)',
                'typical_cost': 50,  # Cheaper options
                'max_positions': int((self.budget - 100) / 50),
                'profit_potential': '100-500%',
                'success_rate': '15-25%',
                'timeframe': '1-4 weeks'
            },
            
            'straddles_iwm': {
                'description': 'Buy IWM straddles (volatility play)',
                'typical_cost': 300,  # Call + Put
                'max_positions': int((self.budget - 100) / 300),
                'profit_potential': '25-150%',
                'success_rate': '40-50%',
                'timeframe': '2-4 weeks'
            },
            
            'weekly_scalps': {
                'description': 'Weekly options scalping',
                'typical_cost': 25,  # Very short term
                'max_positions': int((self.budget - 100) / 25),
                'profit_potential': '20-100%',
                'success_rate': '35-45%',
                'timeframe': '1-5 days'
            }
        }
        
        # Calculate realistic position sizes
        for strategy_name, strategy in strategies.items():
            cost_with_commission = strategy['typical_cost'] + self.commission_per_contract
            strategy['cost_with_commission'] = cost_with_commission
            strategy['commission_impact'] = round(self.commission_per_contract / strategy['typical_cost'] * 100, 1)
            
            logger.info(f"{strategy_name}: ${cost_with_commission} per position, {strategy['commission_impact']}% commission impact")
        
        return strategies
    
    async def recommend_optimal_strategy(self):
        """Recommend optimal strategy based on current market conditions"""
        
        # Get current market data
        spy = yf.Ticker("SPY")
        vix = yf.Ticker("^VIX")
        
        spy_hist = spy.history(period="30d")
        vix_hist = vix.history(period="30d")
        
        if spy_hist.empty or vix_hist.empty:
            return {"error": "Could not get market data"}
        
        # Current market conditions
        spy_30d_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0] - 1) * 100
        current_vix = vix_hist['Close'].iloc[-1]
        vix_30d_avg = vix_hist['Close'].mean()
        
        # Market regime analysis
        market_trend = "bullish" if spy_30d_return > 2 else "bearish" if spy_30d_return < -2 else "sideways"
        vol_regime = "high" if current_vix > vix_30d_avg * 1.2 else "low" if current_vix < vix_30d_avg * 0.8 else "normal"
        
        recommendations = {
            'market_analysis': {
                'spy_30d_return': round(spy_30d_return, 2),
                'current_vix': round(current_vix, 2),
                'vix_30d_avg': round(vix_30d_avg, 2),
                'market_trend': market_trend,
                'volatility_regime': vol_regime
            }
        }
        
        # Strategy recommendations based on conditions
        if vol_regime == "high" and market_trend == "bearish":
            recommendations['primary_strategy'] = {
                'name': 'IWM Put Buying',
                'reasoning': 'High volatility + bearish trend = good put buying opportunity',
                'position_size': '$200-300 per trade',
                'max_positions': 3,
                'target_return': '50-150%',
                'risk_level': 'Medium-High'
            }
            
        elif vol_regime == "low" and market_trend == "bullish":
            recommendations['primary_strategy'] = {
                'name': 'IWM Call Buying',
                'reasoning': 'Low volatility + bullish trend = cheap calls with momentum',
                'position_size': '$150-250 per trade',
                'max_positions': 4,
                'target_return': '30-100%',
                'risk_level': 'Medium'
            }
            
        elif vol_regime == "high":
            recommendations['primary_strategy'] = {
                'name': 'Short-term Volatility Scalping',
                'reasoning': 'High volatility = large intraday moves to capture',
                'position_size': '$100-200 per trade',
                'max_positions': 5,
                'target_return': '20-80%',
                'risk_level': 'High'
            }
            
        else:
            recommendations['primary_strategy'] = {
                'name': 'Mixed Directional Plays',
                'reasoning': 'Neutral conditions = wait for clear signals',
                'position_size': '$150-250 per trade',
                'max_positions': 3,
                'target_return': '25-75%',
                'risk_level': 'Medium'
            }
        
        # Alternative if selling RTX shares
        rtx = yf.Ticker("RTX")
        rtx_price = rtx.history(period="1d")['Close'].iloc[-1]
        rtx_proceeds = 9 * rtx_price
        
        recommendations['rtx_liquidation_strategy'] = {
            'rtx_current_price': round(rtx_price, 2),
            'proceeds_from_9_shares': round(rtx_proceeds, 2),
            'total_liquid_capital': round(rtx_proceeds + self.budget, 2),
            'enhanced_strategy': 'With more capital, could do small credit spreads or larger option positions'
        }
        
        return recommendations

async def main():
    """Run market research analysis"""
    research = MarketResearch()
    
    # Analyze current prices
    prices = await research.analyze_current_prices()
    
    # Analyze options strategies  
    strategies = await research.analyze_options_strategies()
    
    # Get recommendations
    recommendations = await research.recommend_optimal_strategy()
    
    # Print results
    print("\n" + "="*60)
    print("🔍 MARKET RESEARCH FOR $1000 BUDGET")
    print("="*60)
    
    print("\n📊 Current Asset Prices:")
    for symbol, data in prices.items():
        print(f"  {symbol}: ${data['current_price']} - Can afford {data['affordable_shares']} shares")
    
    print("\n🎯 Options Strategy Analysis:")
    for name, strategy in strategies.items():
        print(f"  {name}: ${strategy['cost_with_commission']} per position, {strategy['max_positions']} max positions")
    
    print("\n💡 Current Market Recommendation:")
    rec = recommendations['primary_strategy']
    print(f"  Strategy: {rec['name']}")
    print(f"  Reasoning: {rec['reasoning']}")
    print(f"  Position Size: {rec['position_size']}")
    print(f"  Max Positions: {rec['max_positions']}")
    
    if 'rtx_liquidation_strategy' in recommendations:
        rtx_data = recommendations['rtx_liquidation_strategy']
        print(f"\n🔄 RTX Liquidation Option:")
        print(f"  RTX Price: ${rtx_data['rtx_current_price']}")
        print(f"  9 Shares Worth: ${rtx_data['proceeds_from_9_shares']}")
        print(f"  Total Capital: ${rtx_data['total_liquid_capital']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())