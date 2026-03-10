import asyncio

from strategies.arbitrage.funding_arbitrage import FundingRateArbitrage


def test_funding_arbitrage_compat_adapter() -> None:
    adapter = FundingRateArbitrage(
        {
            "enabled": True,
            "min_funding_rate": 0.00001,
            "min_annual_yield": 0.0,
            "funding_interval": 8,
            "capital": 10_000,
        }
    )

    async def _run() -> None:
        await adapter.update_funding_rates(
            "binance",
            [
                {
                    "symbol": "BTCUSDT",
                    "fundingRate": 0.0003,
                    "fundingTime": 4_102_444_800_000,  # year 2100 for deterministic freshness
                    "predictedRate": 0.00025,
                }
            ],
        )
        opportunities = await adapter.find_opportunities(
            spot_prices={"BTCUSDT": 45_000.0},
            perp_prices={"BTCUSDT": 44_990.0},
        )
        assert len(opportunities) >= 1
        summary = adapter.get_funding_summary()
        assert "binance" in summary
        assert summary["binance"]["count"] == 1

    asyncio.run(_run())
