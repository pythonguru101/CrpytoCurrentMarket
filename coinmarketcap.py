#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import time
import libcoinmarketcap
import libdb_mysql


db = libdb_mysql.libdb_mysql()
mkt = libcoinmarketcap.libcoinmarketcap()


######################################################################################################################
## MAIN


mkt.init_coinmarketcap()

fecha = str(time.strftime("%Y-%m-%d",time.localtime()))
hora = str(time.strftime("%H:%M:%S",time.localtime()))

result = mkt.get_coinmarketcap()

if result <> -1:
    data = mkt.parse_page(result, mkt.tickers, {'fecha': fecha, 'hora': hora})

    if data <> -1:
        params1 = {'last_flag': 0}
        params2 = {'last_flag': 1}
        db.generic_update(params1, params2, "capitalization")

        print("Coinmarketcap controller:")
        for i in range(0, len(data)):
            print data[i]
            if data[i]['volume'] is None:
                data[i]['volume'] = 0.00
            data[i]['volume'] = '%10.4f' % data[i]['volume']
            data[i]['last_flag'] = 1
        db.generic_row_insert(data, "capitalization")

sys.exit()

