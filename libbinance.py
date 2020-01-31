#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import sys
import time
import requests
import decimal
import libdb_mysql

db = libdb_mysql.libdb_mysql()


class libbinance:
    "Class to capture streaming data in real time from Binance"

    # -- constructor --
    def __init__(self):
        self.debug_mode = 1
        self.tickers = []
        self.controller = {}

        self.market = {
            'name': "Binance",
            'controller': "BINANCE",
            'preintticker': "BI-",
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


    # -- binance init --
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


    # -- get binance JSON page --
    def get_exchange(self):
        url = ""
        page = []

        url = "https://api.binance.com/api/v1/ticker/allPrices"
        response = requests.get(url)
        prices = response.json()

        url = "https://api.binance.com/api/v1/ticker/allBookTickers"
        response = requests.get(url)
        askbid = response.json()

        if 'code' in prices:
            if prices['code'] < 0:
                print("Error in page!!")
                return -1

        for i in self.tickers:
            for n in prices:
                if i['remoteticker'] == n['symbol']:
                    price = n['price']
            for n in askbid:
                if i['remoteticker'] == n['symbol']:
                    page.append({'ticker': i['localticker'], 'price': price, 'bidprice': n['bidPrice'],
                                 'askprice': n['askPrice'], 'bidvol': n['bidQty'], 'askvol': n['askQty']})

        if self.debug_mode >= 1:
            print
            print("-------------------------------------------------------------------------------------------")
            print(page)
            print("-------------------------------------------------------------------------------------------")

        return page


    # -- parse binance page --
    def parse_page(self, page):
        self.values_list = []
        dollarvalue = decimal.Decimal(0.00)

        fullfecha = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        tmpsecs = time.strptime(fullfecha, "%Y-%m-%d %H:%M:%S")
        secs = time.mktime(tmpsecs)

        for i in page:
            if i['ticker'] == "BI-BTCUSDT":
                dollarvalue = decimal.Decimal(i['price'])

        for i in page:
            if i['ticker'] == "BI-BTCUSDT":
                dollars = decimal.Decimal(i['price'])
            else:
                dollars = decimal.Decimal(i['price']) * dollarvalue

            self.tick = {
                'ticker': i['ticker'],
                'secs': secs,
                'last': decimal.Decimal(i['price']),
                'dollars': dollars,
                'dayvol': 0.00,
                'last_flag': 1
            }
            self.values_list.append(self.tick)

            if self.debug_mode >= 1:
                print("libBINANCE:")
                print(self.values_list[-1])

        return self.values_list


    # -- get Binance historical data --
    def get_historical(self):
        alldata = []
        mongo, ddbb = self.open_db()
        tickers_t = ddbb.tickers

        tickers = list(tickers_t.find({'$and': [{'active': "1"}, {"controller": "BINANCE"}]}))
        for i in tickers:
            url = "https://api.binance.com/api/v1/klines?symbol=" + i['remoteticker'] + "&interval=1m"

            result = requests.get(url)

            for n in result.json():
                n.append(i['remoteticker'])
                alldata.append(n)

        return alldata


    # -- parse historical --
    def parse_historical(self, data):
        values_list = []

        for i in data:
            local_ticker = self.ticker_conversion(i[12])

            if local_ticker != "":
                secs = int(str(i[6])[0:10])
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
        base_url = "https://api.binance.com/api/v1/trades?symbol="

        # -- tickers loop --
        for i in self.tickers:
            url = base_url + i['remoteticker']
            print(url)
            result = requests.get(url, timeout=(5, 5))
            data = result.json()

            # -- get and convert data --
            if len(data) > 0:
                limit = int(time.time()) - 300
                buyvolume = 0.00
                sellvolume = 0.00
                for n in data:
                    seconds = n['time']
                    if int(seconds) >= limit:
                        if n['isBuyerMaker'] == True:
                            buyvolume += float(n['qty'])
                        if n['isBuyerMaker'] == False:
                            sellvolume += float(n['qty'])

                tmp = {
                    'ticker': i['localticker'],
                    'secs': int(time.time()),
                    'buyvolume': buyvolume,
                    'sellvolume': sellvolume
                }
                volumes.append(tmp)

            time.sleep(0.1)

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
        mkt_data = []
        response = requests.get("https://api.binance.com/api/v1/exchangeInfo")
        data = response.json()

        for i in data['symbols']:
            mkt_data.append({'market': i['symbol'], 'currency': i['baseAsset'], 'min_size': 0.00, 'min_notional': 0.00,
                             'decimals': 0, 'lot_size': 0.00})

        return mkt_data


