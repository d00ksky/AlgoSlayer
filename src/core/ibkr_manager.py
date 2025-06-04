"""
Interactive Brokers Connection Manager
Smart connection with trading mode awareness and yfinance fallback
"""
import asyncio
import yfinance as yf
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from config.trading_config import config, TradingModeConfig, IBKRConfig

class IBKRManager:
    """Smart IBKR connection manager with fallback capabilities"""
    
    def __init__(self):
        self.ib = None
        self.connected = False
        self.connection_attempted = False
        self.last_connection_attempt = None
        self.trading_mode = TradingModeConfig.load_from_env()
        
        logger.info(f"🏦 IBKR Manager initialized")
        logger.info(f"📊 Mode: {self.trading_mode.get_mode_description()}")
    
    async def connect(self) -> bool:
        """Smart connection respecting trading modes"""
        
        if not self.trading_mode.should_connect_ibkr():
            logger.info("🏦 IBKR connection not required for current mode")
            return False
        
        self.connection_attempted = True
        self.last_connection_attempt = datetime.now()
        
        try:
            # Import ib_insync only when needed
            from ib_insync import IB
            
            logger.info(f"🏦 Attempting IBKR connection...")
            logger.info(f"🔗 Connecting to {IBKRConfig.get_connection_string()}")
            
            self.ib = IB()
            
            # Set timeout for connection
            await asyncio.wait_for(
                self._attempt_connection(),
                timeout=IBKRConfig.TIMEOUT
            )
            
            if self.ib.isConnected():
                self.connected = True
                logger.success(f"✅ IBKR connected successfully!")
                logger.info(f"📊 Account: {self.get_account_summary()}")
                return True
            else:
                logger.warning("⚠️ IBKR connection failed - will use fallback data")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(f"⏰ IBKR connection timeout ({IBKRConfig.TIMEOUT}s)")
            return False
        except ImportError:
            logger.error("❌ ib_insync not installed - using fallback only")
            return False
        except Exception as e:
            logger.warning(f"⚠️ IBKR connection error: {e}")
            return False
    
    async def _attempt_connection(self):
        """Internal connection attempt"""
        port = IBKRConfig.get_port()
        await self.ib.connectAsync(
            host=IBKRConfig.HOST,
            port=port,
            clientId=IBKRConfig.CLIENT_ID
        )
    
    def get_account_summary(self) -> str:
        """Get account information"""
        if not self.connected or not self.ib:
            return "Not connected"
        
        try:
            account_values = self.ib.accountSummary()
            
            # Extract key values
            net_liquidation = "N/A"
            buying_power = "N/A"
            
            for item in account_values:
                if item.tag == "NetLiquidation" and item.currency == "USD":
                    net_liquidation = f"${float(item.value):,.2f}"
                elif item.tag == "BuyingPower" and item.currency == "USD":
                    buying_power = f"${float(item.value):,.2f}"
            
            mode = "Paper" if IBKRConfig.get_port() == IBKRConfig.PAPER_PORT else "Live"
            return f"{mode} - Net: {net_liquidation}, Buying Power: {buying_power}"
            
        except Exception as e:
            logger.error(f"🏦 Error getting account summary: {e}")
            return "Error retrieving account data"
    
    async def get_market_data(self, symbol: str = "RTX") -> Dict:
        """Get market data from IBKR or yfinance fallback"""
        
        # Try IBKR first if connected
        if self.connected and self.ib:
            try:
                ibkr_data = await self._get_ibkr_data(symbol)
                if ibkr_data:
                    return ibkr_data
            except Exception as e:
                logger.warning(f"🏦 IBKR data error: {e}, falling back to yfinance")
        
        # Fallback to yfinance
        return await self._get_yfinance_data(symbol)
    
    async def _get_ibkr_data(self, symbol: str) -> Optional[Dict]:
        """Get data from IBKR"""
        try:
            from ib_insync import Stock
            
            # Create contract
            contract = Stock(symbol, "SMART", "USD")
            
            # Get market data
            self.ib.qualifyContracts(contract)
            ticker = self.ib.reqMktData(contract)
            
            # Wait for data
            await asyncio.sleep(2)
            
            if ticker.last:
                return {
                    "symbol": symbol,
                    "price": float(ticker.last),
                    "bid": float(ticker.bid) if ticker.bid else None,
                    "ask": float(ticker.ask) if ticker.ask else None,
                    "volume": int(ticker.volume) if ticker.volume else None,
                    "timestamp": datetime.now().isoformat(),
                    "source": "IBKR"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"🏦 IBKR data retrieval error: {e}")
            return None
    
    async def _get_yfinance_data(self, symbol: str) -> Dict:
        """Get data from yfinance (always works)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            return {
                "symbol": symbol,
                "price": float(current_price) if current_price else 0.0,
                "bid": info.get('bid'),
                "ask": info.get('ask'),
                "volume": info.get('volume'),
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "timestamp": datetime.now().isoformat(),
                "source": "yfinance"
            }
            
        except Exception as e:
            logger.error(f"📊 yfinance error: {e}")
            return {
                "symbol": symbol,
                "price": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "source": "yfinance_error"
            }
    
    async def place_order(self, order_data: Dict) -> Dict:
        """Place order with safety checks"""
        
        # Check if trading is allowed
        if not self.trading_mode.is_safe_to_trade():
            return {
                "status": "BLOCKED",
                "reason": f"Trading disabled: {self.trading_mode.get_mode_description()}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check IBKR connection for actual trading
        if not self.connected:
            if self.trading_mode.IBKR_REQUIRED:
                return {
                    "status": "FAILED",
                    "reason": "IBKR connection required but not available",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "SIMULATED",
                    "reason": "No IBKR connection - order simulated",
                    "order_data": order_data,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Place actual order via IBKR
        return await self._place_ibkr_order(order_data)
    
    async def _place_ibkr_order(self, order_data: Dict) -> Dict:
        """Place order via IBKR"""
        try:
            from ib_insync import Stock, MarketOrder, LimitOrder
            
            symbol = order_data.get("symbol", "RTX")
            action = order_data.get("action", "BUY")  # BUY or SELL
            quantity = order_data.get("quantity", 1)
            order_type = order_data.get("type", "MKT")  # MKT or LMT
            limit_price = order_data.get("limit_price")
            
            # Create contract
            contract = Stock(symbol, "SMART", "USD")
            self.ib.qualifyContracts(contract)
            
            # Create order
            if order_type == "MKT":
                order = MarketOrder(action, quantity)
            else:
                order = LimitOrder(action, quantity, limit_price)
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            return {
                "status": "PLACED",
                "order_id": trade.order.orderId,
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "order_type": order_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"🏦 Order placement error: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_connection_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            "connected": self.connected,
            "connection_attempted": self.connection_attempted,
            "last_attempt": self.last_connection_attempt.isoformat() if self.last_connection_attempt else None,
            "trading_mode": self.trading_mode.get_mode_description(),
            "ibkr_required": self.trading_mode.IBKR_REQUIRED,
            "should_connect": self.trading_mode.should_connect_ibkr(),
            "can_trade": self.trading_mode.is_safe_to_trade(),
            "fallback_available": True,  # yfinance always available
            "connection_string": IBKRConfig.get_connection_string()
        }
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected and self.ib:
            try:
                self.ib.disconnect()
                self.connected = False
                logger.info("🏦 IBKR disconnected")
            except Exception as e:
                logger.error(f"🏦 Disconnect error: {e}")

# Global IBKR manager instance
ibkr_manager = IBKRManager() 