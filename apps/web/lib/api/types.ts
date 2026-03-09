export interface AccountSummary {
  account_id: string;
  equity: number;
  cash: number;
  buying_power: number;
}

export interface Position {
  symbol: string;
  qty: number;
  avg_price: number;
  market_price: number;
  unrealized_pnl: number;
}

export interface Order {
  order_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  status: string;
  created_at: string;
}

export interface Fill {
  fill_id: string;
  order_id: string;
  symbol: string;
  quantity: number;
  price: number;
  timestamp: string;
}

export interface RiskState {
  kill_switch_active: boolean;
  kill_switch_reason: string;
  current_drawdown: number;
  daily_pnl: number;
}
