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
        pd.read_csv(r"C:\Users\romch\Downloads\Bitstamp_BTCUSDT_1h.csv")[
            "open"
        ].tolist()
    ).reshape(-1, 1)
    open_eth_data = np.array(
        pd.read_csv(r"C:\Users\romch\Downloads\Bitstamp_ETHUSDT_1h.csv")[
            "open"
        ].tolist()
    )

    prep_btc_data = (open_btc_data - open_btc_data[0]) / open_btc_data[0]
    prep_eth_data = (open_eth_data - open_eth_data[0]) / open_eth_data[0]

    global REGR_COEF
    REGR_COEF = LinearRegression().fit(prep_btc_data, prep_eth_data).coef_[0]


async def get_live_quotes():

    prev_noticed_change = 0
    url = "wss://fstream.binance.com/stream?streams={}@kline_{i}/{}@kline_{i}".format(
        *CURRENCIES, i=INTERVAL
    )

    async with websockets.connect(url) as client:
        while True:

            data = json.loads(await client.recv())["data"]["k"]
            open_, close = map(float, (data["o"], data["c"]))

            if data["s"] == "BTCUSDT":
                btc_diff = (close - open_) / open_
                btc_epoch = data["t"]
                both_recieved_cond = 1

            elif data["s"] == "ETHUSDT":
                eth_diff = (close - open_) / open_
                eth_epoch = data["t"]
                both_recieved_cond += 2

            # print(data)

            if not both_recieved_cond % 3:

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
