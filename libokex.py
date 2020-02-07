#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import time
import json
import decimal
import requests
import libdb_mysql

db = libdb_mysql.libdb_mysql()


class libokex:
    "Class to capture streaming data in real time from Okex"

    # -- constructor --
    def __init__(self):
        self.debug_mode = 1
        self.tickers = []
        self.controller = {}

        self.market = {
            'name': "Okex",
            'controller': "OKEX",
            'preintticker': "OK-",
            'grouped': 1,
            'active': 1,
            'timepace': 300,
            'fee': 0.00,
            'ticker_buy': 'L',
            'api_key': '',
            'api_secret': '',
            'passphrase': ''
        }

        self.tick = {
            'ticker': "",
            'secs': 0,
            'last': 0.0000,
            'dollars': 0.0000,
            'dayvol': 0.0000,
            'last_flag': 0
        }

        return


    # -- Okex init --
    def init_exchange(self):
        params = [
            "active=1",
            "controller='" + self.market['controller'] + "'",
            "ORDER BY remoteticker"
        ]
        self.tickers = db.generic_select(params, "tickers")

        params = ["controller='" + self.market['controller'] + "'"]
        tmp = db.generic_select(params, "controllers")
        if len(tmp) > 0:
            self.controller = tmp[0]

        return


    # -- get Okex JSON page --
    def get_exchange(self):
        url = "https://www.okex.com/api/spot/v3/instruments/ticker"
        page = []

        result = requests.get(url)
        page = result.json()

        if self.debug_mode >= 1:
            print
            print("-------------------------------------------------------------------------------------------")
            print(page)
            print("-------------------------------------------------------------------------------------------")

        return page


    # -- parse Okex page --
    def parse_page(self, page):
        values_list = []

        for i in page:
            if i['instrument_id'].upper() == "BTC-USDT":
                dollar_value = float(i['last'])

        for i in page:
            local_ticker = self.ticker_conversion(i['instrument_id'].upper())

            if local_ticker != "":
                if local_ticker == "OK-BTC-USDT":
                    dollars = i['last']
                else:
                    dollars = float(i['last']) * dollar_value

                tick = {
                    'ticker': local_ticker,
                    'secs': int(time.time()),
                    'last': i['last'],
                    'dollars': dollars,
                    'dayvol': i['base_volume_24h'],
                    'last_flag': 1
                }
                values_list.append(tick)

                if self.debug_mode >= 1:
                    print("libOKEX:")
                    print(values_list[-1])

        return values_list


    # -- get Okex historical data --
    def get_historical(self):
        alldata = []

        # for i in self.tickers:
        i = self.tickers[0]
        # url = "https://www.okex.com/api/v1/kline.do?symbol="+i['remoteticker'].lower()+"&type=5min&size=1000"
        url = ""
        print("URL:")
        print(url)

        result = requests.get(url)

        for n in result.json():
            alldata.append(n)

        return alldata


    # -- parse historical --
    def parse_historical(self, data):
        values_list = []

        for i in data:
            local_ticker = self.ticker_conversion(i[6])

            if local_ticker != "":
                secs = int(str(i[0])[0:10])
                pdate = time.strftime("%Y-%m-%d", time.localtime(secs))
                ptime = time.strftime("%H:%M:%S", time.localtime(secs))

                tick = {
                    'ticker': local_ticker,
                    'pdate': pdate,
                    'ptime': ptime,
                    'secs': secs,
                    'open': float(i[1]),
                    'high': float(i[2]),
                    'low': float(i[3]),
                    'close': float(i[4]),
                    'volume': i[5],
                }
                values_list.append(tick)

        return values_list


    # -- get buy and sell volumes --
    def get_volumes(self):
        volumes = []
        page = ""
        base_url = "https://www.okex.com/api/spot/v3/instruments/"  # BTC-USDT/trades?limit=100

        # -- tickers loop --
        for i in self.tickers:
            url = base_url + i['remoteticker'] + "/trades?limit=100"
            print(url)
            result = requests.get(url, timeout=(3, 5))
            data = result.json()

            # -- get and convert data --
            if len(data) > 0 \
                    and not 'message' in data:
                limit = int(time.time()) - 300
                buyvolume = 0.00
                sellvolume = 0.00
                for n in data:
                    datehour = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(n['time'][:19], "%Y-%m-%dT%H:%M:%S"))
                    seconds = self.get_secs(datehour)
                    if int(seconds) >= limit:
                        if n['side'] == "buy":
                            buyvolume += float(n['size'])
                        if n['side'] == "sell":
                            sellvolume += float(n['size'])

                tmp = {
                    'ticker': i['localticker'],
                    'secs': int(time.time()),
                    'buyvolume': buyvolume,
                    'sellvolume': sellvolume
                }
                volumes.append(tmp)

            time.sleep(1)

        return volumes


    # -- conversion table between tickers --
    def ticker_conversion(self, ticker):
        new_ticker = ""

        for i in self.tickers:
            if i['remoteticker'] == ticker:
                new_ticker = i['localticker']

        return new_ticker


    # -- get market tickers --
    def get_exchange_tickers(self):
        url = "https://www.okex.com/api/spot/v3/instruments"
        mkt_data = []
        response = requests.get(url)
        data = response.json()

        for i in data:
            mkt_data.append({'market': i['instrument_id'].upper(), 'currency': i['quote_currency'], 'min_size': 0.00,
                             'min_notional': 0.00, 'decimals': 0, 'lot_size': 0.00})

        return mkt_data


    # -- convert date into seconds --
    def get_secs(self, datehour):
        tmp = datehour.split(" ")
        date = tmp[0]
        hour = tmp[1]
        if len(hour) < 8:
            hour = "0" + hour

        tmpsecs = time.strptime(date + " " + hour, "%Y-%m-%d %H:%M:%S")
        secs = time.mktime(tmpsecs)

        return secs


