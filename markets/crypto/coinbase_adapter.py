# Coinbase Pro Market Adapter
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CoinbaseAdapter:
    """
    Coinbase Pro / Advanced Trade adapter for crypto trading.
    """
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str, sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.sandbox = sandbox
        
        # Base URLs
        if sandbox:
            self.base_url = "https://api-public.sandbox.exchange.coinbase.com"
        else:
            self.base_url = "https://api.exchange.coinbase.com"
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"CoinbaseAdapter initialized: sandbox={sandbox}")
    
    async def connect(self):
        """Establish connection"""
        self.session = aiohttp.ClientSession()
        
        try:
            # Test connection
            await self.get_accounts()
            logger.info("Coinbase connection successful")
        except Exception as e:
            logger.error(f"Coinbase connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _sign_request(self, method: str, path: str, body: str = "") -> Dict:
        """Generate request signature"""
        import hmac
        import hashlib
        import base64
        import json
        
        timestamp = str(datetime.utcnow().timestamp())
        message = timestamp + method.upper() + path + body
        
        hmac_key = base64.b64decode(self.api_secret)
        signature = hmac.new(
            hmac_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': base64.b64encode(signature).decode('utf-8'),
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, path: str, params: dict = None) -> dict:
        """Make API request"""
        if not self.session:
            raise RuntimeError("Not connected")
        
        url = f"{self.base_url}{path}"
        headers = self._sign_request(method, path)
        
        async with self.session.request(method, url, headers=headers, params=params) as response:
            data = await response.json()
            
            if response.status != 200:
                logger.error(f"Coinbase API error: {data}")
                raise Exception(f"API error: {data}")
            
            return data
    
    async def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        return await self._request('GET', '/accounts')
    
    async def get_balance(self, currency: str) -> float:
        """Get balance for specific currency"""
        accounts = await self.get_accounts()
        for account in accounts:
            if account['currency'] == currency:
                return float(account['available'])
        return 0.0
    
    async def get_orderbook(self, symbol: str, level: int = 2) -> Dict:
        """Get order book"""
        path = f"/products/{symbol}/book"
        return await self._request('GET', path, {'level': level})
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data"""
        path = f"/products/{symbol}/ticker"
        return await self._request('GET', path)
    
    async def get_candles(self, symbol: str, granularity: int = 3600) -> List[List]:
        """Get historical candles [time, low, high, open, close, volume]"""
        path = f"/products/{symbol}/candles"
        return await self._request('GET', path, {'granularity': granularity})
    
    async def place_order(self, symbol: str, side: str, order_type: str,
                         quantity: float, price: Optional[float] = None) -> Dict:
        """Place order"""
        path = "/orders"
        
        body = {
            'product_id': symbol,
            'side': side.lower(),
            'size': str(quantity)
        }
        
        if order_type.upper() == 'LIMIT':
            body['type'] = 'limit'
            body['price'] = str(price)
            body['post_only'] = True
        else:
            body['type'] = 'market'
        
        import json
        headers = self._sign_request('POST', path, json.dumps(body))
        
        async with self.session.post(
            f"{self.base_url}{path}", 
            headers=headers, 
            json=body
        ) as response:
            data = await response.json()
            
            if response.status != 200:
                logger.error(f"Order placement error: {data}")
                raise Exception(f"Order error: {data}")
            
            return data
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        path = f"/orders/{order_id}"
        return await self._request('DELETE', path)
    
    async def get_open_orders(self) -> List[Dict]:
        """Get open orders"""
        return await self._request('GET', '/orders')
    
    async def get_fills(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get recent fills"""
        params = {}
        if symbol:
            params['product_id'] = symbol
        return await self._request('GET', '/fills', params=params)
