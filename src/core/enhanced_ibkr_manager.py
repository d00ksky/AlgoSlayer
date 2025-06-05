"""
Enhanced IBKR Manager for RTX Trading
Handles both stock shares and options trading with Interactive Brokers
Supports the high-conviction strategy: hold RTX shares + selective options trades
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yfinance as yf
import pandas as pd

# IBKR imports (install with: pip install ib_insync)
try:
    from ib_insync import IB, Stock, Option, MarketOrder, LimitOrder, Order
    from ib_insync import Contract, PortfolioItem
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    print("⚠️  ib_insync not installed. Install with: pip install ib_insync")

class TradeType(Enum):
    SHARE_BUY = "share_buy"
    SHARE_SELL = "share_sell"
    OPTION_BUY = "option_buy"
    OPTION_SELL = "option_sell"

class TradeMode(Enum):
    PAPER = "paper"
    LIVE = "live"

@dataclass
class RTXPosition:
    symbol: str
    position_type: str  # 'stock', 'call', 'put'
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    
@dataclass
class TradeOrder:
    symbol: str
    trade_type: TradeType
    quantity: int
    order_type: str  # 'market', 'limit'
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = 'DAY'
    
    # Options specific
    strike: Optional[float] = None
    expiry: Optional[str] = None  # YYYYMMDD format
    option_type: Optional[str] = None  # 'call' or 'put'

@dataclass
class TradeResult:
    order_id: int
    status: str  # 'submitted', 'filled', 'cancelled', 'rejected'
    filled_quantity: int
    avg_fill_price: float
    commission: float
    timestamp: datetime
    error_message: Optional[str] = None

class EnhancedIBKRManager:
    """
    Enhanced IBKR Manager for RTX-focused trading
    Supports the strategy: hold 9 RTX shares + selective options trades
    """
    
    def __init__(self, mode: TradeMode = TradeMode.PAPER, port: int = 7497):
        self.mode = mode
        self.port = port  # 7497 for paper, 7496 for live
        self.logger = logging.getLogger(__name__)
        
        # Trading parameters
        self.symbol = "RTX"
        self.target_shares = 9  # Hold 9 RTX shares as base position
        self.max_option_investment = 400  # Max $400 per options trade
        self.max_daily_loss = 200  # Max $200 daily loss limit
        
        # Connection
        self.ib = None
        self.connected = False
        
        # Position tracking
        self.positions = {}
        self.orders = {}
        self.daily_pnl = 0.0
        
        # Safety checks
        self.daily_loss_exceeded = False
        self.trading_enabled = True
        
    async def connect(self) -> bool:
        """Connect to IBKR"""
        if not IBKR_AVAILABLE:
            self.logger.error("ib_insync not installed. Cannot connect to IBKR.")
            return False
        
        try:
            self.ib = IB()
            
            # Connect to TWS or IB Gateway
            if self.mode == TradeMode.PAPER:
                self.logger.info("🔗 Connecting to IBKR Paper Trading...")
                await self.ib.connectAsync('127.0.0.1', 7497, clientId=1)
            else:
                self.logger.info("🔗 Connecting to IBKR Live Trading...")
                await self.ib.connectAsync('127.0.0.1', 7496, clientId=1)
            
            self.connected = True
            self.logger.info(f"✅ Connected to IBKR ({self.mode.value} mode)")
            
            # Get account info
            account_info = await self._get_account_info()
            self.logger.info(f"💰 Account Value: ${account_info.get('total_value', 0):,.2f}")
            
            # Update positions
            await self._update_positions()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            self.logger.info("🔌 Disconnected from IBKR")
    
    async def ensure_rtx_base_position(self) -> bool:
        """
        Ensure we have the target number of RTX shares (9 shares)
        This is our stable base position
        """
        try:
            if not self.connected:
                await self.connect()
            
            # Get current RTX position
            current_shares = await self._get_rtx_shares()
            shares_needed = self.target_shares - current_shares
            
            if shares_needed == 0:
                self.logger.info(f"✅ RTX base position correct: {current_shares} shares")
                return True
            
            elif shares_needed > 0:
                # Need to buy more shares
                self.logger.info(f"📈 Need to buy {shares_needed} RTX shares")
                result = await self.place_stock_order(TradeType.SHARE_BUY, shares_needed)
                return result.status == 'filled'
            
            else:
                # Have too many shares (shouldn't happen in normal operation)
                self.logger.warning(f"⚠️  Have {-shares_needed} extra RTX shares")
                return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring RTX base position: {e}")
            return False
    
    async def place_options_trade(self, trade_decision) -> TradeResult:
        """
        Place options trade based on high-conviction signal
        Only trades when decision.trade_worthy = True
        """
        try:
            if not trade_decision.trade_worthy:
                return TradeResult(
                    order_id=0,
                    status='rejected',
                    filled_quantity=0,
                    avg_fill_price=0.0,
                    commission=0.0,
                    timestamp=datetime.now(),
                    error_message="Not a trade-worthy signal"
                )
            
            # Safety checks
            if not await self._safety_checks():
                return self._create_rejected_result("Safety checks failed")
            
            # Determine option parameters
            option_params = await self._determine_option_parameters(trade_decision)
            if not option_params:
                return self._create_rejected_result("Could not determine option parameters")
            
            # Calculate position size
            position_size = await self._calculate_option_position_size(option_params)
            if position_size == 0:
                return self._create_rejected_result("Position size too small")
            
            # Create option contract
            option_contract = await self._create_option_contract(option_params)
            if not option_contract:
                return self._create_rejected_result("Could not create option contract")
            
            # Place the order
            if trade_decision.action == 'BUY':
                trade_type = TradeType.OPTION_BUY
            else:  # SELL
                trade_type = TradeType.OPTION_BUY  # We buy puts for bearish trades
                option_params['option_type'] = 'put'
            
            order = TradeOrder(
                symbol=self.symbol,
                trade_type=trade_type,
                quantity=position_size,
                order_type='limit',
                limit_price=option_params['limit_price'],
                strike=option_params['strike'],
                expiry=option_params['expiry'],
                option_type=option_params['option_type']
            )
            
            result = await self._execute_option_order(order, option_contract)
            
            # Log the trade
            self._log_options_trade(trade_decision, order, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing options trade: {e}")
            return self._create_rejected_result(f"Trade error: {e}")
    
    async def place_stock_order(self, trade_type: TradeType, quantity: int) -> TradeResult:
        """Place stock order for RTX shares"""
        try:
            if not self.connected:
                await self.connect()
            
            # Create stock contract
            stock = Stock(self.symbol, 'SMART', 'USD')
            
            # Qualify the contract
            await self.ib.qualifyContractsAsync(stock)
            
            # Create order
            if trade_type == TradeType.SHARE_BUY:
                order = MarketOrder('BUY', quantity)
            else:  # SHARE_SELL
                order = MarketOrder('SELL', quantity)
            
            # Place order
            trade = self.ib.placeOrder(stock, order)
            
            # Wait for fill (with timeout)
            await asyncio.wait_for(trade.filledEvent, timeout=30.0)
            
            result = TradeResult(
                order_id=trade.order.orderId,
                status='filled',
                filled_quantity=trade.orderStatus.filled,
                avg_fill_price=trade.orderStatus.avgFillPrice,
                commission=0.0,  # Will be updated later
                timestamp=datetime.now()
            )
            
            self.logger.info(f"✅ Stock order filled: {trade_type.value} {quantity} shares at ${result.avg_fill_price:.2f}")
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning("⏰ Order timeout - may still be pending")
            return self._create_rejected_result("Order timeout")
        except Exception as e:
            self.logger.error(f"Error placing stock order: {e}")
            return self._create_rejected_result(f"Stock order error: {e}")
    
    async def _get_rtx_shares(self) -> int:
        """Get current RTX share position"""
        try:
            positions = self.ib.positions()
            for pos in positions:
                if pos.contract.symbol == self.symbol and pos.contract.secType == 'STK':
                    return int(pos.position)
            return 0
        except Exception as e:
            self.logger.error(f"Error getting RTX position: {e}")
            return 0
    
    async def _safety_checks(self) -> bool:
        """Perform safety checks before trading"""
        try:
            # Check if trading is enabled
            if not self.trading_enabled:
                self.logger.warning("⚠️  Trading disabled")
                return False
            
            # Check daily loss limit
            if self.daily_loss_exceeded:
                self.logger.warning("⚠️  Daily loss limit exceeded")
                return False
            
            # Check market hours (RTX trades on NYSE)
            if not await self._is_market_open():
                self.logger.warning("⚠️  Market is closed")
                return False
            
            # Check account buying power
            account_info = await self._get_account_info()
            if account_info.get('buying_power', 0) < 100:
                self.logger.warning("⚠️  Insufficient buying power")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in safety checks: {e}")
            return False
    
    async def _determine_option_parameters(self, trade_decision) -> Optional[Dict]:
        """Determine option strike, expiry, and type based on trade decision"""
        try:
            # Get current RTX price
            rtx_price = await self._get_current_price()
            if not rtx_price:
                return None
            
            # Calculate strike based on expected move
            expected_move = abs(trade_decision.expected_move)
            
            if trade_decision.action == 'BUY':
                # Call options - slightly out of the money
                strike_price = rtx_price * (1 + expected_move * 0.5)
                option_type = 'call'
            else:  # SELL signal
                # Put options - slightly out of the money
                strike_price = rtx_price * (1 - expected_move * 0.5)
                option_type = 'put'
            
            # Round strike to nearest $2.50 (typical RTX option spacing)
            strike_price = round(strike_price / 2.5) * 2.5
            
            # Determine expiry (2-4 weeks out for liquidity)
            expiry_date = datetime.now() + timedelta(days=21)  # 3 weeks
            expiry_str = expiry_date.strftime('%Y%m%d')
            
            # Get option quote for limit price
            option_price = await self._get_option_price(option_type, strike_price, expiry_str)
            if not option_price:
                return None
            
            # Set limit price (mid-point of bid-ask, or market price + small buffer)
            limit_price = option_price * 1.02  # 2% above market price
            
            return {
                'option_type': option_type,
                'strike': strike_price,
                'expiry': expiry_str,
                'limit_price': limit_price,
                'market_price': option_price
            }
            
        except Exception as e:
            self.logger.error(f"Error determining option parameters: {e}")
            return None
    
    async def _calculate_option_position_size(self, option_params: Dict) -> int:
        """Calculate how many option contracts to trade"""
        try:
            option_price = option_params['market_price']
            max_investment = self.max_option_investment
            
            # Each option contract represents 100 shares
            contracts = int(max_investment / (option_price * 100))
            
            # Minimum 1 contract, maximum based on investment limit
            return max(1, min(contracts, 3))  # Max 3 contracts per trade
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0
    
    async def _create_option_contract(self, option_params: Dict):
        """Create IBKR option contract"""
        try:
            option = Option(
                symbol=self.symbol,
                lastTradeDateOrContractMonth=option_params['expiry'],
                strike=option_params['strike'],
                right=option_params['option_type'].upper(),
                exchange='SMART'
            )
            
            # Qualify the contract
            contracts = await self.ib.qualifyContractsAsync(option)
            if contracts:
                return contracts[0]
            else:
                self.logger.error("Could not qualify option contract")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating option contract: {e}")
            return None
    
    async def _execute_option_order(self, order: TradeOrder, contract) -> TradeResult:
        """Execute the option order"""
        try:
            # Create IBKR order
            if order.order_type == 'limit':
                ib_order = LimitOrder(
                    action='BUY' if order.trade_type == TradeType.OPTION_BUY else 'SELL',
                    totalQuantity=order.quantity,
                    lmtPrice=order.limit_price
                )
            else:
                ib_order = MarketOrder(
                    action='BUY' if order.trade_type == TradeType.OPTION_BUY else 'SELL',
                    totalQuantity=order.quantity
                )
            
            # Place the order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Wait for fill or timeout
            await asyncio.wait_for(trade.filledEvent, timeout=60.0)
            
            return TradeResult(
                order_id=trade.order.orderId,
                status='filled',
                filled_quantity=trade.orderStatus.filled,
                avg_fill_price=trade.orderStatus.avgFillPrice,
                commission=0.0,
                timestamp=datetime.now()
            )
            
        except asyncio.TimeoutError:
            return self._create_rejected_result("Option order timeout")
        except Exception as e:
            return self._create_rejected_result(f"Option execution error: {e}")
    
    async def _get_current_price(self) -> Optional[float]:
        """Get current RTX stock price"""
        try:
            stock = Stock(self.symbol, 'SMART', 'USD')
            await self.ib.qualifyContractsAsync(stock)
            
            ticker = self.ib.reqMktData(stock)
            await asyncio.sleep(2)  # Wait for data
            
            if ticker.last:
                return float(ticker.last)
            elif ticker.close:
                return float(ticker.close)
            else:
                # Fallback to yfinance
                rtx = yf.Ticker(self.symbol)
                data = rtx.history(period="1d")
                if not data.empty:
                    return float(data['Close'].iloc[-1])
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting current price: {e}")
            return None
    
    async def _get_option_price(self, option_type: str, strike: float, expiry: str) -> Optional[float]:
        """Get current option price"""
        try:
            option = Option(
                symbol=self.symbol,
                lastTradeDateOrContractMonth=expiry,
                strike=strike,
                right=option_type.upper(),
                exchange='SMART'
            )
            
            contracts = await self.ib.qualifyContractsAsync(option)
            if not contracts:
                return None
            
            ticker = self.ib.reqMktData(contracts[0])
            await asyncio.sleep(3)  # Wait for option data
            
            if ticker.last:
                return float(ticker.last)
            elif ticker.bid and ticker.ask:
                return (float(ticker.bid) + float(ticker.ask)) / 2
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting option price: {e}")
            return None
    
    async def _is_market_open(self) -> bool:
        """Check if market is open (simplified)"""
        now = datetime.now()
        
        # Basic check: weekdays, 9:30 AM - 4:00 PM ET
        if now.weekday() >= 5:  # Weekend
            return False
        
        hour = now.hour
        return 9 <= hour <= 16  # Simplified market hours
    
    async def _get_account_info(self) -> Dict:
        """Get account information"""
        try:
            if not self.connected:
                return {}
            
            account_values = self.ib.accountValues()
            
            info = {}
            for av in account_values:
                if av.tag == 'TotalCashValue':
                    info['cash'] = float(av.value)
                elif av.tag == 'NetLiquidation':
                    info['total_value'] = float(av.value)
                elif av.tag == 'BuyingPower':
                    info['buying_power'] = float(av.value)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {}
    
    async def _update_positions(self):
        """Update current positions"""
        try:
            if not self.connected:
                return
            
            positions = self.ib.positions()
            self.positions = {}
            
            for pos in positions:
                if pos.contract.symbol == self.symbol:
                    self.positions[pos.contract.conId] = RTXPosition(
                        symbol=pos.contract.symbol,
                        position_type='stock' if pos.contract.secType == 'STK' else 'option',
                        quantity=int(pos.position),
                        avg_cost=float(pos.avgCost),
                        current_price=0.0,  # Will be updated with market data
                        market_value=float(pos.marketValue),
                        unrealized_pnl=float(pos.unrealizedPNL),
                        realized_pnl=0.0
                    )
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def _create_rejected_result(self, error_msg: str) -> TradeResult:
        """Create a rejected trade result"""
        return TradeResult(
            order_id=0,
            status='rejected',
            filled_quantity=0,
            avg_fill_price=0.0,
            commission=0.0,
            timestamp=datetime.now(),
            error_message=error_msg
        )
    
    def _log_options_trade(self, decision, order: TradeOrder, result: TradeResult):
        """Log options trade details"""
        self.logger.info(f"🎯 OPTIONS TRADE EXECUTED")
        self.logger.info(f"   Signal: {decision.action} ({decision.confidence:.1%} confidence)")
        self.logger.info(f"   Option: {order.option_type.upper()} ${order.strike} exp {order.expiry}")
        self.logger.info(f"   Quantity: {result.filled_quantity} contracts")
        self.logger.info(f"   Price: ${result.avg_fill_price:.2f}")
        self.logger.info(f"   Investment: ${result.avg_fill_price * result.filled_quantity * 100:.2f}")
        self.logger.info(f"   Status: {result.status}")
    
    async def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        await self._update_positions()
        
        rtx_shares = await self._get_rtx_shares()
        total_positions = len(self.positions)
        
        summary = {
            'rtx_shares': rtx_shares,
            'target_shares': self.target_shares,
            'shares_on_target': rtx_shares == self.target_shares,
            'total_positions': total_positions,
            'connected': self.connected,
            'mode': self.mode.value,
            'trading_enabled': self.trading_enabled
        }
        
        return summary

# Global IBKR manager instance
ibkr_manager = EnhancedIBKRManager(mode=TradeMode.PAPER)

async def test_ibkr_manager():
    """Test the IBKR manager"""
    print("🔗 Testing Enhanced IBKR Manager")
    print("=" * 40)
    
    try:
        # Test connection
        connected = await ibkr_manager.connect()
        if connected:
            print("✅ Connected to IBKR")
            
            # Test portfolio summary
            summary = await ibkr_manager.get_portfolio_summary()
            print(f"📊 Portfolio Summary:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
            
            # Test RTX base position
            await ibkr_manager.ensure_rtx_base_position()
            
        else:
            print("❌ Failed to connect to IBKR")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await ibkr_manager.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ibkr_manager())