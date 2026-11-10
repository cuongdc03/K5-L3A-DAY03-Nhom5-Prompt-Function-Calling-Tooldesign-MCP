from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_crypto_price(coin_id: str = "bitcoin", currency: str = "usd") -> dict[str, Any]:
    try:
        clean_coin = (coin_id or "").strip().lower() if isinstance(coin_id, str) else ""
        if not clean_coin:
            raise ValueError("Missing or empty coin_id for crypto_price")
        clean_curr = (currency or "usd").strip().lower() if isinstance(currency, str) else "usd"
        if not clean_curr:
            clean_curr = "usd"
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": clean_coin, "vs_currencies": clean_curr}
        headers = {"User-Agent": "AI20k-ResearchAgent/1.0 (educational lab)"}
        resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        price = data.get(clean_coin, {}).get(clean_curr)
        if price is None:
            return {
                "tool": "crypto_price",
                "coin": clean_coin,
                "currency": clean_curr,
                "price": None,
                "message": f"Price not found for coin '{clean_coin}' in '{clean_curr}'",
            }
        return {
            "tool": "crypto_price",
            "coin": clean_coin,
            "currency": clean_curr,
            "price": price,
            "formatted": f"{price} {clean_curr.upper()}",
        }
    except Exception as exc:
        return err("crypto_price", exc)
