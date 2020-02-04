#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import sys
import os
import time
import requests
import libdb_mysql

db = libdb_mysql.libdb_mysql()


class libhuobi:
    "Class to capture streaming data in real time from Huobi.pro"

    # -- constructor --
    def __init__(self):
        self.debug_mode = 1
        self.tickers = []
        self.controller = {}

        self.market = {
            'name': "Huobi",
            'controller': "HUOBI",
            'preintticker': "HB-",
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


    # -- Huobi.pro init --
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


    # -- get Huobi.pro JSON page --
    def get_exchange(self):
        url = "https://api.huobi.pro/market/tickers"
        page = []

        response = requests.get(url)
        page = response.json()

        if self.debug_mode >= 1:
            print
            print("-------------------------------------------------------------------------------------------")
            print(page)
            print("-------------------------------------------------------------------------------------------")

        # -- manage errors on page  --
        # if page.find("success\":false") > 0:
        #       print "Error in page!!!"
        #       return -1

        return page


    # -- parse Huobi.pro page --
    def parse_page(self, page):
        values_list = []

        for i in page['data']:
            if i['symbol'].upper() == "BTCUSDT":
                dollar_value = i['close']

        for i in page['data']:
            local_ticker = self.ticker_conversion(i['symbol'].upper())

            if local_ticker != "":
                if local_ticker == "HB-BTCUSDT":
                    dollars = i['close']
                else:
                    dollars = i['close'] * dollar_value

                secs = int(time.time())

                self.tick = {
                    'ticker': local_ticker,
                    'secs': secs,
                    'last': i['close'],
                    'dollars': dollars,
                    'dayvol': i['vol'],
                    'last_flag': 1
                }
                values_list.append(self.tick)

                if self.debug_mode > 1:
                    print("libHuobi:")
                    print(values_list[-1])

        return values_list


    # -- get Huobi historical data --
    def get_historical(self):
        alldata = []
        mongo, ddbb = self.open_db()
        tickers_t = ddbb.tickers

        tickers = list(tickers_t.find({'$and': [{'active': "1"}, {"controller": "HUOBI"}]}))
        for i in tickers:
            url = "https://api.huobi.pro/market/history/kline?symbol=" + i[
                'remoteticker'].lower() + "&period=1min&size=1000"
            result = requests.get(url)

            for n in result.json()['data']:
                n['ticker'] = i['remoteticker']
                alldata.append(n)

        return alldata


    # -- parse historical --
    def parse_historical(self, data):
        values_list = []

        for i in data:
            local_ticker = self.ticker_conversion(i['ticker'])

            if local_ticker != "":
                secs = int(i['id'])
                pdate = time.strftime("%Y-%m-%d", time.localtime(secs))
                ptime = time.strftime("%H:%M:%S", time.localtime(secs))

                tick = {
                    'ticker': local_ticker,
                    'pdate': pdate,
                    'ptime': ptime,
                    'secs': secs,
                    'open': float(i['open']),
                    'high': float(i['high']),
                    'low': float(i['low']),
                    'close': float(i['close']),
                    'volume': i['vol'],
                }
                values_list.append(tick)

        return values_list


    # -- get buy and sell volumes --
    def get_volumes(self):
        volumes = []
        page = ""
        base_url = "https://api.huobi.pro/market/history/trade?symbol="

        # -- tickers loop --
        for i in self.tickers:
            url = base_url + i['remoteticker'].lower() + "&size=100"
            print url
            result = requests.get(url, timeout=(5, 5))
            data = result.json()

            # -- get and convert data --
            if len(data['data']) > 0:
                limit = int(time.time()) - 300
                buyvolume = 0.00
                sellvolume = 0.00
                for m in data['data']:
                    for n in m['data']:
                        seconds = int(str(n['ts'])[0:10])
                        if int(seconds) >= limit:
                            if n['direction'] == "buy":
                                buyvolume += float(n['amount'])
                            if n['direction'] == "sell":
                                sellvolume += float(n['amount'])

                tmp = {
                    'ticker': i['localticker'],
                    'secs': seconds,
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


    # -- get exchange tickers --
    def get_exchange_tickers(self):
        mkt_data = []
        response = requests.get("https://api.huobi.pro/market/tickers")
        data = response.json()

        for i in data['data']:
            mkt_data.append(
                {'market': i['symbol'].upper(), 'currency': '', 'min_size': 0.00, 'min_notional': 0.00, 'decimals': 0,
                 'lot_size': 0.00})

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


