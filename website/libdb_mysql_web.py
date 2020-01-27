#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import time
import os
import base64
import csv
import re
import json
import MySQLdb
#import pymysql
import decimal
import pandas as pd
from operator import itemgetter


# -- class for web page database functions --
class libdb_mysql:
    "Class for web page database functions"

    # -- constructor --
    def __init__(self):
        self.path = ""
        self.debug_mode = 1
        self.launcher = ""
        self.stopper = ""

        return


    ### DATABASE FUNCTIONS ###

    # -- open database --
    def open_db(self):
        user = ""
        password = ""
        self.path = os.getcwd() + "/"
        pwfile = self.path + "../auth.pk"
        database = "ccmarket"

        bbdd = MySQLdb.connect(host="localhost", user="juanlu", passwd="", db=database)
        # bbdd = MySQLdb.connect(host="192.168.2.200", user="root", passwd="weareafamily", db=database)
        #bbdd = pymysql.connect(host="localhost", user="juanlu", passwd="", db=database)
        if os.path.isfile(pwfile):
            csv_list = []
            fp = open(pwfile, "r")
            reader = csv.DictReader(fp)

            for i in reader:
                csv_list.append(i)
            fp.close()
            user = base64.b64decode(csv_list[0]['user'])
            password = base64.b64decode(csv_list[0]['password'])

            if csv_list[0]['user'] != "" \
                    and csv_list[0]['password'] != "":
                bbdd = MySQLdb.connect(host="localhost", user=user, passwd=password, db=database)
                # bbdd = MySQLdb.connect(host="192.168.2.200", user=user, passwd=password, db=database)
                #bbdd = pymysql.connect(host="localhost", user=user, passwd=password, db=database)

        sql = bbdd.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        #sql = bbdd.cursor(pymysql.cursors.DictCursor)

        return bbdd, sql


    # -- insert quotes data on db --
    def generic_row_insert(self, data, table):
        # -- open database --
        bbdd, sql = self.open_db()

        # -- get and filter data --
        for i in data:
            query = "INSERT INTO " + table + " ("
            for n in i.keys():
                query += n + ","
            query = query[0:-1]

            query += ") VALUES ("
            for n in i.keys():
                query += "'" + str(i[n]) + "',"

            query = query[0:-1]
            query += ");"

            if self.debug_mode >= 1:
                print(query)

            sql.execute(query)

        bbdd.commit()

        bbdd.close()

        return


    # -- make generic select defined by data content --
    def generic_select(self, data, table):
        bbdd, sql = self.open_db()

        query = "SELECT * FROM " + table + " WHERE "

        for i in data:
            if i.upper().find("SELECT") == 0:
                query = i + " FROM " + table + " WHERE "

            if i.find("SELECT") < 0 \
                    and i.find("ORDER BY") < 0 \
                    and i.find("GROUP BY") < 0:
                query += i + " AND "

            if i.find("GROUP BY") == 0:
                if query[-5:] == " AND ":
                    query = query[0:-5]
                if query[-7:] == " WHERE ":
                    query = query[0:-7]
                query += " " + i

            if i.find("ORDER BY") == 0:
                if query[-5:] == " AND ":
                    query = query[0:-5]
                if query[-7:] == " WHERE ":
                    query = query[0:-7]
                query += " " + i

        if query[-5:] == " AND ":
            query = query[0:-5]
        if query[-7:] == " WHERE ":
            query = query[0:-7]

        query += ";"
        if self.debug_mode > 1:
            print(query)

        sql.execute(query)
        tuplas = sql.fetchall()

        bbdd.close()

        if tuplas is None:
            return []
        if len(tuplas) == 0:
            return []

        return tuplas


    # -- make a generic delete defined by data content --
    def generic_delete(self, data, table):
        bbdd, sql = self.open_db()

        query = "DELETE FROM " + table

        if len(data) > 0:
            query += " WHERE "

            for i in data:
                query += i + " AND "
            query = query[0:-5]

        query += ";"
        if self.debug_mode > 1:
            print(query)

        sql.execute(query)
        bbdd.commit()

        bbdd.close()

        return


    # -- make a generic update defined by two data content --
    def generic_update(self, data1, data2, table):
        bbdd, sql = self.open_db()

        query = "UPDATE " + table

        if len(data1) > 0:
            query += " SET "

            for i in data1.keys():
                query += "`" + i + "`=" + str(data1[i]) + ", "
            query = query[0:-2]

        if len(data2) > 0:
            query += " WHERE "

            for i in data2:
                if str(data2[i]).upper().find("LIKE") >= 0:
                    query += "`" + i + "` '" + str(i) + "' AND "
                else:
                    query += "`" + i + "`='" + str(i) + "' AND "
            query = query[0:-5]

        query += ";"
        if self.debug_mode > 1:
            print(query)

        sql.execute(query)
        bbdd.commit()

        bbdd.close()

        return


    def fill_tickers_tmp(self, origin_table, dest_table):
        bbdd, sql = self.open_db()

        query = "INSERT INTO " + dest_table + " SELECT * FROM " + origin_table + ";"
        print(query)
        sql.execute(query)
        bbdd.commit()

        bbdd.close()

        return


    # -- get search tickers from each tickers table --
    def get_search_tickers(self, active, table, controller, search):
        sqlsearch = ""
        sqlactive = ""

        params = ["controller='" + controller + "'"]
        if search != "":
            search = re.sub("\*", "%", search)
            params.append("remoteticker LIKE '" + search + "'")
        if active == "1":
            params.append("AND active=1")
        params.append("ORDER BY controller, remoteticker")
        tickers = self.generic_select(params, table)

        return tickers


    # -- update ticker by id --
    def update_ticker_by_id(self, ticker):
        params1 = {}

        for i in ticker.keys():
            if i != "id":
                params1[i] = ticker[i]
        params2 = ["id=" + str(ticker['id'])]
        self.generic_update(params1, params2, "tickers_tmp")

        return


    # -- update all tickers in controller by search --
    def update_controller_active(self, controller, search, active):
        params1 = {'active': active}
        params2 = ["controller='" + controller + "'"]

        if search != "":
            search = re.sub("\*", "%", search)
            params2.append("remoteticker LIKE '" + search + "'")
        self.generic_update(params1, params2, "tickers_tmp")

        return


    # -- get all ticker ids by search --
    def get_ticker_id_search(self, controller, search):
        params = [
            "SELECT id",
            "controller='" + controller + "'"
        ]

        if search != "":
            search = re.sub("\*", "%", search)
            params.append("remoteticker LIKE '" + search + "'")
        tickers = self.generic_select(params, "tickers")

        ticker_ids = []
        for i in tickers:
            ticker_ids.append(i['id'])

        return ticker_ids


    # -- get last prices by secs --
    def get_prices_by_secs(self, ticker):
        params = [
            "ticker='" + ticker + "'",
            "ORDER BY secs DESC LIMIT 1 OFFSET 0"
        ]
        price = self.generic_select(params, "prices")

        return price[0]

    # -- get ticker data --
    def get_ticker_data(self, ticker, timeframe, sfrom, sto):
        params = ["ticker='" + ticker + "'"]

        if sfrom != "":
            params.append("secs>" + str(sfrom))

        if sto != "":
            params.append("secs<" + str(sto))
        prices = self.generic_select(params, "prices")

        if prices is None:
            return []

        # -- add date and time to data if not exist --
        if not 'pdate' in prices \
                or not 'ptime' in prices:
            newprices = []
            for i in prices:
                i['pdate'] = time.strftime("%Y-%m-%d", i['secs'])
                i['ptime'] = time.strftime("%H:%M:%S", i['secs'])
                newprices.append(i)
        prices = newprices

        # -- get OHLC --
        pricesdf = pd.DataFrame(prices)
        pricesdf['time'] = pd.to_datetime(str(pricesdf['pdate']) + ' ' + str(pricesdf['ptime']))
        pricesdf = pricesdf[['time', 'open', 'high', 'low', 'close', 'volume']].copy()
        pricesdf = pricesdf.set_index(['time'])

        if timeframe != "":
            finalprices = pricesdf['close'].resample(timeframe).ohlc().fillna(0.0)
            finalprices['volume'] = pricesdf['volume'].resample(timeframe).sum()

            pricesdf = finalprices

        pricesdf.reset_index(inplace=True)

        return json.loads(pricesdf.to_json(orient='records', date_format='iso'))


