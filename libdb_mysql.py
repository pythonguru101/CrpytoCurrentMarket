#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import base64
import time
import MySQLdb
#import pymysql
import csv


class libdb_mysql:
    "Class for manage mysql database queries"

    # -- constructor --
    def __init__(self):
        self.path = ""
        self.debug_mode = 1

        return


    # -- open database --
    def open_db(self):
        user = ""
        password = ""
        self.path = os.getcwd() + "/"
        pwfile = self.path + "auth.pk"
        database = "ccmarket"

        # bbdd = MySQLdb.connect(host="192.168.2.200", user="root", passwd="weareafamily", db=database)
        bbdd = MySQLdb.connect(host="localhost", user="juanlu", passwd="", db=database)
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
                # bbdd = MySQLdb.connect(host="192.168.2.200", user=user, passwd=password, db=database)
                bbdd = MySQLdb.connect(host="localhost", user=user, passwd=password, db=database)
                # bbdd = pymysql.connect(host="localhost", user=user, passwd=password, db=database)

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

            op_ok = 0
            while op_ok == 0:
                try:
                    sql.execute(query)
                    op_ok = 1
                except:
                    time.sleep(0.1)

        bbdd.commit()

        bbdd.close()

        return


    # -- make a generic insert with one row --
    def generic_insert(self, data, table):
        bbdd, sql = self.open_db()

        query = "INSERT INTO " + table + " ("

        for i in data.keys():
            query += i + ", "
        query = query[0:-2]

        query += ") VALUES ("

        for i in data.keys():
            query += "'" + str(data[i]) + "', "
        query = query[0:-2]

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
                    and i.find("ORDER BY") < 0:
                query += i + " AND "

            if i.find("ORDER BY") == 0:
                if query[-5:] == " AND ":
                    query = query[0:-5]
                query += " " + i

        if query[-5:] == " AND ":
            query = query[0:-5]
        if query[-7:] == " WHERE ":
            query = query[0:-7]

        query += ";"
        if self.debug_mode >= 1:
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
        if self.debug_mode >= 1:
            print(query)

        sql.execute(query)
        bbdd.commit()

        bbdd.close()

        return


    # -- make a generic update defined by two data content --
    def generic_update(self, data1, data2, table):
        bbdd, sql = self.open_db()

        # -- compose query --
        query = "UPDATE " + table

        if len(data1) > 0:
            query += " SET "

            for i in data1.keys():
                query += "`" + i + "`='" + str(data1[i]) + "', "
            query = query[0:-2]

        if len(data2) > 0:
            query += " WHERE "

            for i in data2:
                query += i + " AND "
            if query[-5:] == " AND ":
                query = query[0:-5]

        query += ";"
        if self.debug_mode >= 1:
            print(query)

        # -- execute query --
        count = 0
        while count < 2:
            try:
                sql.execute(query)
            except:
                pass
            count += 1

        bbdd.commit()

        bbdd.close()

        return


