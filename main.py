"""Dip-buy mean-reversion bot for the make.fun BTC race (agent-fun/bars-replay/v1).

Idea: Coinbase Wrapped BTC mean-reverts on the minute scale. The bot watches the
highest close over a trailing window and buys when the price has dipped a clear
percentage below that high. It sells when the price recovers a fixed percentage
above what it paid, and it cuts the trade with a stop-loss when the price keeps
falling. All decisions are integer arithmetic on the raw price units, so two
runs on the same bars produce identical orders. No wall clock, no network, no
files outside the repository; any randomness would be seeded from hello.seed
(this bot uses none).
"""

import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
BPS = 10_000

# Strategy knobs (all in whole bars / basis points).
WINDOW_BARS = 120        # trailing window for the highest close (2 hours)
MIN_HISTORY = 60         # bars of closes needed before the first buy
DIP_BPS = 200            # buy when close is this far below the trailing high (2.0%)
TAKE_PROFIT_BPS = 75     # sell when close is this far above the entry cost (0.75%)
STOP_LOSS_BPS = 100      # sell when close is this far below the entry cost (1.0%)
COOLDOWN_BARS = 30       # bars to wait after a stop-loss before buying again
MAX_SLIPPAGE_BPS = 500   # per-order slippage allowance from the latest close
MIN_NOTIONAL = 1_000_000  # 1 USDC, the smallest buy the replay accepts
TOTAL_BARS = 1440        # the window is 24 hours of 1-minute bars
LATE_CUTOFF_BARS = 60    # no new buys in the last N bars (no time left to exit)


class DipBuyBot:
    """State for one run. All state is rebuilt from the batches the harness sends."""

    def __init__(self):
        self.closes = deque(maxlen=WINDOW_BARS)
        self.bar_index = 0
        self.last_stop_bar = -10 ** 9
        self.qty_scale = 8
        self.price_scale = 5
        self.quote_scale = 6

    def on_hello(self, state):
        """Read the asset scales out of hello so the entry-price math is exact."""
        sym = state.symbols.get(SYMBOL)
        if sym is not None:
            self.qty_scale = sym["qty_scale"]
            self.price_scale = sym["price_scale"]
        self.quote_scale = state.hello["capital"]["quote_scale"]

    def entry_price(self, state):
        """Average entry price (raw price units) from the position's cost.

        cost is what was actually paid, fees included, so the take-profit and
        stop-loss triggers below are measured against the true break-even.
        """
        pos = state.positions.get(SYMBOL)
        if pos is None or pos.qty == 0:
            return None
        numerator = pos.cost * (10 ** (self.qty_scale + self.price_scale))
        denominator = pos.qty * (10 ** self.quote_scale)
        return numerator // denominator

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        self.bar_index += 1

        # Warm-up bars build history only; their orders would be rejected.
        if state.warming_up:
            return []
        if len(self.closes) < MIN_HISTORY:
            return []

        high = max(self.closes)
        pos = state.positions.get(SYMBOL)
        holding = pos is not None and pos.qty > 0
        orders = []

        if not holding:
            # Flat: buy the dip, unless we just stopped out and are cooling off.
            if self.bar_index - self.last_stop_bar < COOLDOWN_BARS:
                return []
            # No time left to exit a new trade near the end of the window.
            if self.bar_index >= TOTAL_BARS - LATE_CUTOFF_BARS:
                return []
            # The dip: close far below the trailing high.
            if close * BPS <= high * (BPS - DIP_BPS):
                spend = min(state.cash, state.weight_room(SYMBOL))
                if spend >= MIN_NOTIONAL:
                    orders.append(
                        {
                            "side": "buy",
                            "symbol": SYMBOL,
                            "notional_quote_units": spend,
                            "max_slippage_bps": MAX_SLIPPAGE_BPS,
                        }
                    )
        else:
            entry = self.entry_price(state)
            if entry is None:
                return []
            if close * BPS >= entry * (BPS + TAKE_PROFIT_BPS):
                orders.append(
                    {
                        "side": "sell",
                        "symbol": SYMBOL,
                        "qty": pos.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                )
            elif close * BPS <= entry * (BPS - STOP_LOSS_BPS):
                self.last_stop_bar = self.bar_index
                orders.append(
                    {
                        "side": "sell",
                        "symbol": SYMBOL,
                        "qty": pos.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                )
        return orders


bot = DipBuyBot()
makefun_bars.run(bot.on_batch, on_hello=bot.on_hello)
