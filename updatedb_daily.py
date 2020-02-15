#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import libdb_mysql


db = libdb_mysql.libdb_mysql()


######################################################################################################################
## MAIN


# -- delete opportunities --
begin = int(time.time())
params = ["secs<="+str(begin)]
db.generic_delete(params, "opportunities")


# -- get tickers --
params = []
tickers = db.generic_select(params, "tickers")


# -- delete each ticker with more than 1 hour data --
for i in tickers:
	print("Deleting "+i['localticker'])
	secs = int(time.time()) - 3600

	params = [
		"ticker='"+i['localticker']+"'",
		"secs<"+str(secs)
	]
	db.generic_delete(params, "prices")

