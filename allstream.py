#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import libmultifeed
import libdb_mysql

mtf = libmultifeed.libmultifeed()
db = libdb_mysql.libdb_mysql()


# -- FUNCTION TO GET ARGUMENTS --
def arguments(args):
    tokens = {
        'tickers': [],
        'markets': [],
        'verbose': 1
    }

    for i in range(0, len(args)):
        if args[i] == "-h" or args[i] == "--help":
            print(args[0] + " USAGE: ")
            print("-h o --help\tHelp.")
            print("-t o --tickers\tTickers separated by spaces.")
            print("-m o --market\tStart all tickers from market(s) (controller(s)).")
            print("-v o --verbose\tVerbose.")
            sys.exit()
        if args[i] == "-t" or args[i] == "--tickers":
            if len(args) > i:
                for n in range(i + 1, len(args)):
                    if args[n][0] != "-":
                        tokens['tickers'].append(args[n].upper())
                        i = n
        if args[i] == "-m" or args[i] == "--market":
            if len(args) > i:
                for n in range(i + 1, len(args)):
                    if args[n][0] != "-":
                        tokens['markets'].append(args[n].upper())
                        i = n
        if args[i] == "-v" or args[i] == "--verbose":
            tokens['verbose'] = 2

    return tokens


# -- FUNCTION TO WRITE PROCESS LINE TO PROCESS FILE --
def add_process_line(pid, group, tickers):
    pf = open(mtf.process_file, "a")
    line = str(pid) + "\t" + group + "\t" + tickers + "\n"
    "writing line...."
    print(line)
    pf.write(line)
    pf.close()

    return


######################################################################################################################
## MAIN


# -- PROCESS ARGUMENTS --
args = sys.argv
argums = arguments(args)
mtf.debug_mode = argums['verbose']

os.environ['TZ'] = 'Europe/Madrid'
process_list = []

# -- ASSIGN PATHS --
mtf.path = os.getcwd()
mtf.process_file = mtf.path + "multifeed-process.txt"

# -- GET TICKER CONFIGURATION --
params = ["active=1"]

if len(argums['tickers']) == 0 and len(argums['markets']) == 0:
    mtf.kill_all_process()

    mtf.tickers_list = db.generic_select(params, "tickers")

    for n in mtf.tickers_list:
        if n['controller'] not in mtf.controllers:
            mtf.controllers += (n['controller'].upper(),)

if len(argums['markets']) > 0:
    for i in argums['markets']:
        params.append("controller='" + i + "'")
        mtf.tickers_list = db.generic_select(params, "tickers")
        mtf.controllers += (i,)

if len(argums['tickers']) > 0:
    tickers_list = db.generic_select(params, "tickers")

    for i in tickers_list:
        for n in argums['tickers']:
            if i['localticker'] == n:
                mtf.tickers_list += (i,)
                mtf.controllers += (i['controller'].upper(),)

# -- LAUNCH PROCESSES FOR TICKERS GROUPED --
for i in mtf.controllers:
    launch_text = "Launching " + i + " process with tickers: "
    tickers = ""
    for n in mtf.tickers_list:
        if n['controller'].upper() == i:
            tickers += n['localticker'] + " "

    func_name = getattr(mtf, "crypto_controller")
    if len(tickers) > 0:
        pid = os.fork()
        if pid == 0:
            func_name(i)
        if pid != 0 and pid not in process_list:
            add_process_line(pid, i, tickers)
            process_list.append(pid)
