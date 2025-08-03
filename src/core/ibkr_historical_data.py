"""
IBKR Historical Data Integration
Fetches real historical options data from Interactive Brokers
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
from ib_insync import IB, Stock, Option, util
import asyncio
from dataclasses import dataclass
import json
import sqlite3

@dataclass 
class HistoricalOptionData:
    """Historical option data point"""
    timestamp: datetime
    symbol: str
    strike: float
    expiry: datetime
    option_type: str
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    underlying_price: float

class IBKRHistoricalDataManager:
    """Manages historical data fetching from IBKR"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 7497, client_id: int = 999):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.cache_db = 'data/ibkr_historical_cache.db'
        self._init_cache_db()
        
    def _init_cache_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp DATETIME,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                vwap REAL,
                bar_count INTEGER,
                UNIQUE(symbol, timestamp)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS option_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp DATETIME,
                strike REAL,
                expiry DATE,
                option_type TEXT,
                bid REAL,
                ask REAL,
                last REAL,
                volume INTEGER,
                open_interest INTEGER,
                implied_volatility REAL,
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                underlying_price REAL,
                UNIQUE(symbol, timestamp, strike, expiry, option_type)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def connect(self):
        """Connect to IBKR Gateway/TWS"""
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)
            logger.info(f"Connected to IBKR on {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib.isConnected():
            self.ib.disconnect()
            logger.info("Disconnected from IBKR")
            
    async def fetch_stock_history(self, symbol: str, end_date: datetime, 
                                 duration: str = '1 Y', bar_size: str = '1 day') -> pd.DataFrame:
        """Fetch historical stock data from IBKR"""
        
        # Check cache first
        cached_data = self._get_cached_stock_data(symbol, end_date, duration)
        if cached_data is not None and len(cached_data) > 0:
            logger.info(f"Using cached stock data for {symbol}")
            return cached_data
            
        logger.info(f"Fetching {symbol} stock history from IBKR: {duration} ending {end_date}")
        
        # Create contract
        stock = Stock(symbol, 'SMART', 'USD')
        
        # Request historical data
        bars = await self.ib.reqHistoricalDataAsync(
            stock,
            endDateTime=end_date,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        
        if not bars:
            logger.warning(f"No historical data returned for {symbol}")
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = util.df(bars)
        df['symbol'] = symbol
        
        # Cache the data
        self._cache_stock_data(df, symbol)
        
        return df
        
    async def fetch_option_chain_history(self, symbol: str, date: datetime, 
                                       strike_range: float = 0.1) -> List[HistoricalOptionData]:
        """Fetch historical option chain data"""
        
        # Check cache first
        cached_data = self._get_cached_option_data(symbol, date)
        if cached_data:
            logger.info(f"Using cached option data for {symbol} on {date}")
            return cached_data
            
        logger.info(f"Fetching {symbol} option chain for {date}")
        
        # Get current stock price for that date
        stock = Stock(symbol, 'SMART', 'USD')
        
        # Get stock price on that date
        stock_bars = await self.ib.reqHistoricalDataAsync(
            stock,
            endDateTime=date,
            durationStr='1 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True
        )
        
        if not stock_bars:
            logger.warning(f"No stock data for {symbol} on {date}")
            return []
            
        stock_price = stock_bars[-1].close
        
        # Get option chain
        chains = await self.ib.reqSecDefOptParamsAsync(
            stock.symbol, '', stock.secType, stock.conId
        )
        
        if not chains:
            logger.warning(f"No option chains found for {symbol}")
            return []
            
        chain = chains[0]
        
        # Filter strikes around current price
        strikes = [s for s in chain.strikes 
                  if stock_price * (1 - strike_range) <= s <= stock_price * (1 + strike_range)]
        
        # Get expirations 15-60 days out
        target_expiries = []
        for exp in chain.expirations:
            exp_date = datetime.strptime(exp, '%Y%m%d')
            days_to_exp = (exp_date - date).days
            if 15 <= days_to_exp <= 60:
                target_expiries.append(exp)
                
        option_data = []
        
        # Fetch data for each option
        for expiry in target_expiries[:3]:  # Limit to 3 expiries to avoid rate limits
            for strike in strikes[:5]:  # Limit strikes
                for right in ['C', 'P']:
                    try:
                        option = Option(symbol, expiry, strike, right, 'SMART')
                        
                        # Get option details
                        [option_contract] = await self.ib.qualifyContractsAsync(option)
                        
                        # Get historical data for this option
                        option_bars = await self.ib.reqHistoricalDataAsync(
                            option_contract,
                            endDateTime=date,
                            durationStr='1 D',
                            barSizeSetting='1 hour',
                            whatToShow='MIDPOINT',
                            useRTH=True
                        )
                        
                        if option_bars:
                            last_bar = option_bars[-1]
                            
                            # Get Greeks (simplified calculation)
                            iv = await self._estimate_iv(option_contract, last_bar.close, stock_price)
                            greeks = self._calculate_greeks(
                                stock_price, strike, 
                                (datetime.strptime(expiry, '%Y%m%d') - date).days,
                                iv, right
                            )
                            
                            option_data.append(HistoricalOptionData(
                                timestamp=date,
                                symbol=symbol,
                                strike=strike,
                                expiry=datetime.strptime(expiry, '%Y%m%d'),
                                option_type=right,
                                bid=last_bar.close - 0.05,  # Estimate bid/ask
                                ask=last_bar.close + 0.05,
                                last=last_bar.close,
                                volume=int(last_bar.volume),
                                open_interest=0,  # Would need separate request
                                implied_volatility=iv,
                                delta=greeks['delta'],
                                gamma=greeks['gamma'],
                                theta=greeks['theta'],
                                vega=greeks['vega'],
                                underlying_price=stock_price
                            ))
                            
                    except Exception as e:
                        logger.debug(f"Error fetching option {symbol} {strike} {expiry} {right}: {e}")
                        continue
                        
        # Cache the data
        if option_data:
            self._cache_option_data(option_data)
            
        return option_data
        
    def _calculate_greeks(self, stock_price: float, strike: float, 
                         days_to_expiry: int, iv: float, option_type: str) -> Dict:
        """Simplified Greeks calculation"""
        from scipy.stats import norm
        
        # Simplified Black-Scholes Greeks
        t = days_to_expiry / 365
        r = 0.05  # Risk-free rate
        
        if t <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
            
        d1 = (np.log(stock_price / strike) + (r + iv**2 / 2) * t) / (iv * np.sqrt(t))
        d2 = d1 - iv * np.sqrt(t)
        
        if option_type == 'C':
            delta = norm.cdf(d1)
        else:
            delta = -norm.cdf(-d1)
            
        gamma = norm.pdf(d1) / (stock_price * iv * np.sqrt(t))
        theta = -(stock_price * norm.pdf(d1) * iv) / (2 * np.sqrt(t)) / 365
        vega = stock_price * norm.pdf(d1) * np.sqrt(t) / 100
        
        return {
            'delta': round(delta, 4),
            'gamma': round(gamma, 4),
            'theta': round(theta, 4),
            'vega': round(vega, 4)
        }
        
    async def _estimate_iv(self, option: Option, option_price: float, stock_price: float) -> float:
        """Estimate implied volatility"""
        # Simplified IV estimation
        moneyness = stock_price / option.strike
        time_to_expiry = (option.lastTradeDateOrContractMonth - datetime.now()).days / 365
        
        if time_to_expiry <= 0:
            return 0.3
            
        # Very rough IV estimate based on price
        if option.right == 'C':
            intrinsic = max(0, stock_price - option.strike)
        else:
            intrinsic = max(0, option.strike - stock_price)
            
        time_value = option_price - intrinsic
        
        # Rough approximation
        iv = time_value / (stock_price * np.sqrt(time_to_expiry) * 0.4)
        
        return max(0.1, min(2.0, iv))  # Cap between 10% and 200%
        
    def _cache_stock_data(self, df: pd.DataFrame, symbol: str):
        """Cache stock data to database"""
        conn = sqlite3.connect(self.cache_db)
        df.to_sql('stock_history', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        
    def _cache_option_data(self, option_data: List[HistoricalOptionData]):
        """Cache option data to database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        for opt in option_data:
            cursor.execute('''
                INSERT OR REPLACE INTO option_history 
                (symbol, timestamp, strike, expiry, option_type, bid, ask, last,
                 volume, open_interest, implied_volatility, delta, gamma, theta, vega, underlying_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opt.symbol, opt.timestamp, opt.strike, opt.expiry, opt.option_type,
                opt.bid, opt.ask, opt.last, opt.volume, opt.open_interest,
                opt.implied_volatility, opt.delta, opt.gamma, opt.theta, opt.vega,
                opt.underlying_price
            ))
            
        conn.commit()
        conn.close()
        
    def _get_cached_stock_data(self, symbol: str, end_date: datetime, duration: str) -> Optional[pd.DataFrame]:
        """Retrieve cached stock data"""
        conn = sqlite3.connect(self.cache_db)
        
        # Parse duration
        duration_days = 365 if '1 Y' in duration else 30
        start_date = end_date - timedelta(days=duration_days)
        
        query = '''
            SELECT * FROM stock_history 
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
        conn.close()
        
        if len(df) > duration_days * 0.7:  # If we have 70% of expected data
            return df
        return None
        
    def _get_cached_option_data(self, symbol: str, date: datetime) -> List[HistoricalOptionData]:
        """Retrieve cached option data"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Allow 1 day tolerance
        date_start = date - timedelta(days=1)
        date_end = date + timedelta(days=1)
        
        cursor.execute('''
            SELECT * FROM option_history 
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
        ''', (symbol, date_start, date_end))
        
        rows = cursor.fetchall()
        conn.close()
        
        option_data = []
        for row in rows:
            option_data.append(HistoricalOptionData(
                timestamp=datetime.fromisoformat(row[2]),
                symbol=row[1],
                strike=row[3],
                expiry=datetime.fromisoformat(row[4]),
                option_type=row[5],
                bid=row[6],
                ask=row[7],
                last=row[8],
                volume=row[9],
                open_interest=row[10],
                implied_volatility=row[11],
                delta=row[12],
                gamma=row[13],
                theta=row[14],
                vega=row[15],
                underlying_price=row[16]
            ))
            
        return option_data

async def fetch_comprehensive_historical_data():
    """Fetch comprehensive historical data for backtesting"""
    
    ibkr = IBKRHistoricalDataManager()
    
    if not await ibkr.connect():
        logger.error("Could not connect to IBKR")
        return
        
    try:
        # Fetch RTX stock history
        end_date = datetime.now()
        stock_data = await ibkr.fetch_stock_history('RTX', end_date, '2 Y', '1 day')
        
        logger.info(f"Fetched {len(stock_data)} days of RTX stock data")
        
        # Fetch option data for key dates (monthly)
        option_data_points = []
        
        # Sample monthly for the last year
        for months_back in range(12):
            sample_date = end_date - timedelta(days=30 * months_back)
            
            logger.info(f"Fetching option chain for {sample_date.date()}")
            options = await ibkr.fetch_option_chain_history('RTX', sample_date)
            
            option_data_points.extend(options)
            
            # Respect rate limits
            await asyncio.sleep(2)
            
        logger.info(f"Fetched {len(option_data_points)} option data points")
        
        # Save to enhanced format
        if option_data_points:
            df_options = pd.DataFrame([
                {
                    'timestamp': opt.timestamp,
                    'symbol': opt.symbol,
                    'strike': opt.strike,
                    'expiry': opt.expiry,
                    'option_type': opt.option_type,
                    'mid_price': (opt.bid + opt.ask) / 2,
                    'bid': opt.bid,
                    'ask': opt.ask,
                    'volume': opt.volume,
                    'iv': opt.implied_volatility,
                    'delta': opt.delta,
                    'gamma': opt.gamma,
                    'theta': opt.theta,
                    'vega': opt.vega,
                    'underlying_price': opt.underlying_price
                }
                for opt in option_data_points
            ])
            
            df_options.to_csv('data/rtx_historical_options_ibkr.csv', index=False)
            logger.info("Saved IBKR historical options data")
            
    finally:
        ibkr.disconnect()

if __name__ == "__main__":
    # Run the historical data fetcher
    asyncio.run(fetch_comprehensive_historical_data())