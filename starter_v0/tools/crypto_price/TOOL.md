---
name: crypto_price
track: bonus
kind: live_api
provider: CoinGecko Public API
requires_env: []
inputs: [coin_id, currency]
outputs: [price]
side_effect: false
---
# crypto_price

Tra cứu tỷ giá và giá tiền mã hóa theo thời gian thực từ CoinGecko API.
