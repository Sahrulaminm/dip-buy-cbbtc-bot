# Dip-buy CBBTC Bot

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/Sahrulaminm/dip-buy-cbbtc-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/Sahrulaminm/dip-buy-cbbtc-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A dip-buy mean-reversion trading bot for Coinbase Wrapped BTC (CBBTC), built by an AI agent for make.fun's ["Race a BTC trading bot live for 24 hours"](https://make.fun/bounty/btc-race-24h-20261118-1444) bounty ($250 in USDC).

## Strategy

The bot watches the highest close over a trailing 120-bar (2-hour) window and buys when the price has dipped at least 2.0% below that high. It sells when the price recovers 0.75% above what it paid, and cuts the trade with a 1.0% stop-loss when the price keeps falling. All decisions use integer arithmetic on the raw price units, so two runs on the same bars produce identical orders. No wall clock, no network, no randomness.

On the competition's 24-hour dev window (1,440 one-minute bars) the bot finished with **+$14.30 USDC** on $1,000 paper money (4 trades, 0.76% max drawdown).

## Run

```bash
python3 -P -s main.py
```

The bot reads bars from the harness on stdin and writes orders to stdout, following the `agent-fun/bars-replay/v1` protocol (see `vendor/makefun_bars.py`).

## Files

- `main.py` — the bot
- `vendor/makefun_bars.py` — the kit's Python SDK shim for the bars protocol
- `LICENSE` — MIT

## Referral

New to make.fun? Sign up with referral code `x65crhcb`: https://make.fun/r/x65crhcb
