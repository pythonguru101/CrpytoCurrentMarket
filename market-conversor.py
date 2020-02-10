#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import requests
import libdb_mysql


class market_conversor:
    # -- constructor --
    def __init__(self):
        self.market = {
            'name': "",
            'controller': "",
            'preintticker': "",
            'active': 1,
            'grouped': 1,
            'timepace': 60,
            'fee': 0.00,
            'ticker_buy': '',
            'api_key': '',
            'api_secret': '',
            'passphrase': ''
        }
        self.old_tickers = []
        self.table = "tickers"
        self.default_active = "0"
        self.newticker_count = 0
        self.debug_mode = 1

        return


    # -- function to get arguments --
    def arguments(self, args):
        tokens = {
            'exchange': "",
            'tickers': [],
            'delete': 0,
            'delete_controller': 0,
            'no_add': 0,
            'activate': 0,
            'verbose': 1
        }

        for i in range(0, len(args)):
            if args[i] == "-h" or args[i] == "--help":
                print(args[0] + " USAGE: ")
                print("-h or --help\tHelp.")
                print("-m or --market\tExchange name.")
                print("-t or --tickers\tTickers list separated by spaces.")
                print("-d or --delete\tDelete all tickers from controller before adding tickers.")
                print("-c or --delete-controller\tDelete controller before adding tickers.")
                print("-n or --no-add\tNo add tickers.")
                print("-a or --activate\tark all new tickers as active.")
                print("-v o --verbose\tVerbose.")
                sys.exit()
            if args[i] == "-m" or args[i] == "--market":
                tokens['exchange'] = args[i + 1]
            if args[i] == "-t" or args[i] == "--tickers":
                if len(args) > i:
                    for n in range(i + 1, len(args)):
                        if args[n][0] != "-":
                            tokens['tickers'].append(args[n].upper())
                            i = n
            if args[i] == "-d" or args[i] == "--delete":
                tokens['delete'] = 1
            if args[i] == "-c" or args[i] == "--delete-controller":
                tokens['delete_controller'] = 1
            if args[i] == "-n" or args[i] == "--no-add":
                tokens['no_add'] = 1
            if args[i] == "-a" or args[i] == "--activate":
                tokens['activate'] = 1
                self.default_active = "1"
            if args[i] == "-v" or args[i] == "--verbose":
                tokens['verbose'] = 2

        return tokens


    ### MARKET AND TICKER MANAGING FUNCTIONS ###

    # -- get markets data --
    def get_markets_json(self, exchange):
        mkt_data = []
        got_exchange = 0

	# -- add COINMARKETCAP coins --
        if exchange == "COINMARKETCAP":
            if 'libcoinmarketcap' not in sys.modules:
                import libcoinmarketcap
                exch = libcoinmarketcap.libcoinmarketcap()
                got_exchange = 1

        # -- add BINANCE tickers --
        if exchange == "BINANCE":
            if 'libbinance' not in sys.modules:
                import libbinance
                exch = libbinance.libbinance()
                got_exchange = 1

        # -- add BITFINEX tickers --
        if exchange == "BITFINEX":
            if 'libbitfinex' not in sys.modules:
                import libbitfinex
                exch = libbitfinex.libbitfinex()
                got_exchange = 1

        # -- add BITTREX tickers --
        if exchange == "BITTREX":
            if 'libbittrex' not in sys.modules:
                import libbittrex
                exch = libbittrex.libbittrex()
                got_exchange = 1

        # -- add OKEX tickers --
        if exchange == "OKEX":
            if 'libokex' not in sys.modules:
                import libokex
                exch = libokex.libokex()
                got_exchange = 1

        # -- add HUOBI tickers --
        if exchange == "HUOBI":
            if 'libhuobi' not in sys.modules:
                import libhuobi
                exch = libhuobi.libhuobi()
                got_exchange = 1

        if got_exchange == 0:
            return -1

        exch.debug_mode = self.debug_mode
        self.market = exch.market
        mkt_data = exch.get_exchange_tickers()

        return mkt_data


    # -- add new tickers to database --
    def add_new_tickers(self, mkt_data):
        new_tickers = []

        # -- get old tickers --
        params = ["controller='" + self.market['controller'] + "'"]
        tickers = db.generic_select(params, "tickers")

        # -- check controller --
        self.check_controller()

        # -- check tickers --
        for i in mkt_data:
            found = 0
            for n in tickers:
                if i['market'] == n['remoteticker']:
                    found = 1
                    print("FOUND " + i['market'] + " not adding!")

            if found == 0:
                new_ticker = {
                    'active': self.default_active,
                    'name': self.market['name'] + " " + i['market'],
                    'localticker': self.market['preintticker'] + i['market'],
                    'remoteticker': i['market'],
                    'controller': self.market['controller'],
                    'retard': 0,
                    'currency': i['currency'],
                    'min_size': i['min_size'],
                    'min_notional': i['min_notional'],
                    'decimals': i['decimals'],
                    'lot_size': i['lot_size']
                }
                new_tickers.append(new_ticker)

        return new_tickers


    ### DATABASE FUNCTIONS ###

    # -- check controller --
    def check_controller(self):
        # -- check controller --
        params = ["controller='" + self.market['controller'] + "'"]
        tmp = db.generic_select(params, "controllers")

        if len(tmp) == 0:
            db.generic_insert(self.market, "controllers")
            print("INSERT CONTROLLER: " + self.market['controller'])
            print("=============================================================")

        return


    # -- disable old tickers --
    def disable_old_tickers(self, mkt_data):
        params = ["controller='" + self.market['controller'] + "'"]
        self.tickers = db.generic_select(params, "tickers")

        for i in self.tickers:
            found = 0
            for n in mkt_data:
                if i['remoteticker'] == n['market']:
                    found = 1

            if found == 0:
                params1 = {
                    'active': self.default_active,
                    'name': i['name'] + " (discontinued)"
                }
                params2 = ["remoteticker='" + i['remoteticker'] + "'"]
                db.generic_update(params1, params2, "tickers")

        return


    # -- insert data on db --
    def insert_data(self, data, exchange):
        new_tickers_count = 0

        # -- check controller --
        self.check_controller()

        # -- insert tickers --
        db.generic_row_insert(data, "tickers")
        for i in data:
            new_tickers_count += 1
            print("INSERT TICKER: " + str(i['name']))
            print("========================================")

        return new_tickers_count


    # -- delete tickers by controller --
    def delete_tickers(self, exchange):
        print("DELETING TICKERS FROM " + exchange + "...")

        params = ["controller='" + exchange + "'"]
        db.generic_delete(params, "tickers")

        return


    # -- delete controller --
    def delete_controller(self, exchange):
        print("DELETING CONTROLLER " + exchange + "...")

        params = ["controller='" + exchange + "'"]
        db.generic_delete(params, "controllers")

        return


##########################################################################
## MAIN


db = libdb_mysql.libdb_mysql()
mc = market_conversor()

# -- process arguments --
args = sys.argv
argums = mc.arguments(args)
#print(argums)
db.debug_mode = argums['verbose']
new_tickers_count = 0

# -- no market --
if argums['exchange'] == "":
    mc.arguments([sys.argv[0], '-h'])
    sys.exit()

# -- delete what is specified --
if argums['delete'] == 1:
    mc.delete_tickers(argums['exchange'])
if argums['delete_controller'] == 1:
    mc.delete_controller(argums['exchange'])
if argums['no_add'] == 1:
    mkt_data = mc.get_markets_json(argums['exchange'])
    mc.check_controller()
    print("No tickers added on " + argums['exchange'] + "!")
    sys.exit()

# -- get markets at exchange selected --
if argums['exchange'] == "YAHOO" \
        or argums['exchange'] == "CNBC":
    mc.tickers = argums['tickers']
mkt_data = mc.get_markets_json(argums['exchange'])

# -- get new tickers and add to db --
if len(mkt_data) == 0:
    print("Exchange not supported! (or bad written)")
    sys.exit()
else:
    new_tickers = mc.add_new_tickers(mkt_data)

if len(new_tickers) > 0:
    new_tickers_count = mc.insert_data(new_tickers, mc.market)

if argums['exchange'] != "KITE":
    # -- disactivate remove old dissapeared tickers (if any) --
    mc.disable_old_tickers(mkt_data)

print(str(new_tickers_count) + " NEW TICKERS ADDED!")


