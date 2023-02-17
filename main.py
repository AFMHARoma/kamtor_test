import asyncio
import json
import time

import numpy as np
import pandas as pd
import websockets
from sklearn.linear_model import LinearRegression

REGR_COEF = 1
CURRENCIES = ["btcusdt", "ethusdt"]
INTERVAL = "1h"


def renew_regr_coef():
    open_btc_data = np.array(
        pd.read_csv(r"Bitstamp_BTCUSDT_1h.csv")["open"].tolist()).reshape(-1, 1)
    open_eth_data = np.array(
        pd.read_csv(r"Bitstamp_ETHUSDT_1h.csv")["open"].tolist())

    prep_btc_data = (open_btc_data - open_btc_data[0]) / open_btc_data[0]
    prep_eth_data = (open_eth_data - open_eth_data[0]) / open_eth_data[0]

    global REGR_COEF
    REGR_COEF = LinearRegression().fit(prep_btc_data, prep_eth_data).coef_[0]


async def get_live_quotes():

    last_update_btc = 0
    last_update_eth = 0
    prev_noticed_change = 0
    url = "wss://fstream.binance.com/stream?streams={}@kline_{i}/{}@kline_{i}".format(
        *CURRENCIES, i=INTERVAL
    )

    async with websockets.connect(url) as client:
        while True:

            data = json.loads(await client.recv())["data"]
            timestamp, spec_data = data['E'], data['k']
            open_, close = map(float, (spec_data["o"], spec_data["c"]))

            if spec_data["s"] == "BTCUSDT":
                btc_diff = (close - open_) / open_
                btc_epoch = spec_data["t"]
                last_update_btc = timestamp

            elif spec_data["s"] == "ETHUSDT":
                eth_diff = (close - open_) / open_
                eth_epoch = spec_data["t"]
                last_update_eth = timestamp

            # print(data)

            if abs(last_update_btc - last_update_eth) <= 300:
                abs_own_growth = (
                    eth_diff - btc_diff * REGR_COEF
                ) * 100 - prev_noticed_change

                if eth_epoch == btc_epoch and abs(abs_own_growth) >= 1:

                    print(
                        f'\n{time.strftime("%Y-%m-%d %H:%M:%S")} -> '
                        f'Собственная цена ETH изменилась на '
                        f'{abs_own_growth:.3f}%\n '
                    )

                    prev_noticed_change = abs_own_growth


if __name__ == "__main__":
    renew_regr_coef()

    asyncio.run(get_live_quotes())
