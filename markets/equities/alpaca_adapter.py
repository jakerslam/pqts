# Alpaca Equity Adapter
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlpacaAdapter:
    """
    Alpaca Markets adapter for equity trading.
    Supports both paper and live trading.
    """
    
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        
        # API URLs
        if paper:
            self.base_url = "https://paper-api.alpaca.markets"
            self.data_url = "https://data.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
            self.data_url = "https://data.alpaca.markets"
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"AlpacaAdapter initialized: paper={paper}")
    
    async def connect(self):
        """Establish connection"""
        self.session = aiohttp.ClientSession()
        
        try:
            await self.get_account()
            logger.info("Alpaca connection successful")
        except Exception as e:
            logger.error(f"Alpaca connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_headers(self) -> Dict:
        """Get authentication headers"""
        return {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
    
    async def _request(self, method: str, url: str, params: dict = None, 
                      use_data_url: bool = False) -> dict:
        """Make API request"""
        if not self.session:
            raise RuntimeError("Not connected")
        
        base = self.data_url if use_data_url else self.base_url
        full_url = f"{base}{url}"
        headers = self._get_headers()
        
        async with self.session.request(method, full_url, headers=headers, params=params) as response:
            data = await response.json()
            
            if response.status != 200:
                logger.error(f"Alpaca API error: {data}")
                raise Exception(f"API error: {data}")
            
            return data
    
    async def get_account(self) -> Dict:
        """Get account information"""
        return await self._request('GET', '/v2/account')
    
    async def get_balance(self) -> float:
        """Get buying power"""
        account = await self.get_account()
        return float(account.get('buying_power', 0))
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        return await self._request('GET', '/v2/positions')
    
    async def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for specific symbol"""
        try:
            return await self._request('GET', f'/v2/positions/{symbol}')
        except Exception:
            return None
    
    async def get_asset(self, symbol: str) -> Dict:
        """Get asset information"""
        return await self._request('GET', f'/v2/assets/{symbol}')
    
    async def get_bars(self, symbol: str, timeframe: str = '1Hour',
                       start: datetime = None, end: datetime = None) -> List[Dict]:
        """Get historical bars"""
        params = {
            'symbols': symbol,
            'timeframe': timeframe
        }
        
        if start:
            params['start'] = start.isoformat()
        if end:
            params['end'] = end.isoformat()
        
        response = await self._request('GET', '/v2/stocks/bars', params, use_data_url=True)
        return response.get('bars', {}).get(symbol, [])
    
    async def get_trades(self, symbol: str, start: datetime, end: datetime) -> List[Dict]:
        """Get historical trades"""
        params = {
            'symbols': symbol,
            'start': start.isoformat(),
            'end': end.isoformat()
        }
        
        response = await self._request('GET', '/v2/stocks/trades', params, use_data_url=True)
        return response.get('trades', {}).get(symbol, [])
    
    async def get_quotes(self, symbol: str, start: datetime, end: datetime) -> List[Dict]:
        """Get historical quotes"""
        params = {
            'symbols': symbol,
            'start': start.isoformat(),
            'end': end.isoformat()
        }
        
        response = await self._request('GET', '/v2/stocks/quotes', params, use_data_url=True)
        return response.get('quotes', {}).get(symbol, [])
    
    async def get_last_trade(self, symbol: str) -> Dict:
        """Get last trade"""
        response = await self._request('GET', f'/v2/stocks/{symbol}/trades/latest', {}, use_data_url=True)
        return response.get('trade', {})
    
    async def get_last_quote(self, symbol: str) -> Dict:
        """Get last quote"""
        response = await self._request('GET', f'/v2/stocks/{symbol}/quotes/latest', {}, use_data_url=True)
        return response.get('quote', {})
    
    async def place_order(self, symbol: str, side: str, qty: float,
                         order_type: str = 'market', 
                         limit_price: Optional[float] = None,
                         stop_price: Optional[float] = None,
                         time_in_force: str = 'day') -> Dict:
        """Place order"""
        url = "/v2/orders"
        
        body = {
            'symbol': symbol,
            'side': side.lower(),
            'type': order_type.lower(),
            'qty': str(qty),
            'time_in_force': time_in_force
        }
        
        if limit_price:
            body['limit_price'] = str(limit_price)
        
        if stop_price:
            body['stop_price'] = str(stop_price)
        
        if not self.session:
            raise RuntimeError("Not connected")
        
        headers = self._get_headers()
        headers['Content-Type'] = 'application/json'
        
        async with self.session.post(
            f"{self.base_url}{url}",
            headers=headers,
            json=body
        ) as response:
            data = await response.json()
            
            if response.status not in [200, 201]:
                logger.error(f"Order error: {data}")
                raise Exception(f"Order error: {data}")
            
            return data
    
    async def get_order(self, order_id: str) -> Dict:
        """Get order status"""
        return await self._request('GET', f'/v2/orders/{order_id}')
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        await self._request('DELETE', f'/v2/orders/{order_id}')
        return True
    
    async def cancel_all_orders(self) -> List[Dict]:
        """Cancel all open orders"""
        return await self._request('DELETE', '/v2/orders')
    
    async def list_orders(self, status: str = 'open', 
                         limit: int = 50) -> List[Dict]:
        """List orders"""
        params = {
            'status': status,
            'limit': limit
        }
        return await self._request('GET', '/v2/orders', params)
    
    async def get_clock(self) -> Dict:
        """Get market clock"""
        return await self._request('GET', '/v2/clock')
    
    async def get_calendar(self, start: str, end: str) -> List[Dict]:
        """Get market calendar"""
        params = {
            'start': start,
            'end': end
        }
        return await self._request('GET', '/v2/calendar', params)
    
    def is_market_open(self, clock_data: Dict) -> bool:
        """Check if market is open"""
        return clock_data.get('is_open', False)
