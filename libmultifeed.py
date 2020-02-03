#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import time
import datetime
import re
import commands
#import subprocess
import libdb_mysql
from operator import itemgetter


db = libdb_mysql.libdb_mysql()


class libmultifeed:
    "Class to capture streaming data in real time"

    # -- constructor --
    def __init__(self):
        self.tickers_list = []
        self.controllers = []
        self.config = []
        self.debug_mode = 2
        self.end_day_time = 22

        self.fh = {
            'fecha': "",
            'hora': "",
            'hor': 0,
            'min': 0,
            'sec': 0,
            'secs': 0,
        }
        self.csv_length = -3
        self.frequency = 5
        self.table = "prices"

        # -- paths, files & programs --
        self.path = os.getcwd()
        self.launcher = self.path + "allstream.py"
        self.process_file = self.path + "multifeed-process.txt"
        self.update_local = self.path + "streams-up.py"

        return


    #### COMMON FUNCTIONS ####

    # -- get config data --
    def get_configuration(self, config):
        config_tickers = []
        tmp_list = []
        lines = config.split("\n")

        i = 0
        while i < len(lines):
            if lines[i].find("#") == -1:
                tmp_list.append(lines[i])
            i += 1
        lines = tmp_list

        for i in range(0, len(lines)):
            if lines[i].find("localticker") == 0:
                ini = lines[i].find("=") + 2
                ticker = lines[i][ini:]
                ini = lines[i + 1].find("=") + 2
                remoteticker = lines[i + 1][ini:]
                ini = lines[i + 2].find("=") + 2
                controller = lines[i + 2][ini:]
                ini = lines[i + 3].find("=") + 2
                retard = int(lines[i + 3][ini:])

                config_tickers.append(
                    {'ticker': ticker, 'remoteticker': remoteticker, 'controller': controller, 'retard': retard})

        return config_tickers


    # -- get fecha hora --
    def get_fecha_hora(self):
        self.fh['fecha'] = str(time.strftime("%Y-%m-%d", time.localtime()))
        self.fh['hora'] = str(time.strftime("%H:%M:%S", time.localtime()))
        self.fh['hor'] = int(time.strftime("%H", time.localtime()))
        self.fh['min'] = int(time.strftime("%M", time.localtime()))
        self.fh['sec'] = int(time.strftime("%S", time.localtime()))

        ftmp = self.fh['fecha'].split("-")
        ahora = datetime.datetime(int(ftmp[0]), int(ftmp[1]), int(ftmp[2]), int(self.fh['hor']), int(self.fh['min']),
                                  int(self.fh['sec']))
        tmpsecs = str(ahora + datetime.timedelta(seconds=+self.frequency))[17:19]

        self.fh['secs'] = int(tmpsecs)
        self.fh['csv_time'] = str(ahora + datetime.timedelta(minutes=self.csv_length))[11:19]

        return


    # -- convert date into seconds --
    def secs(self, datehour):
        tmp = datehour.split(" ")
        date = tmp[0]
        hour = tmp[1]
        if len(hour) < 8:
            hour = "0" + hour

        tmpsecs = time.strptime(date + " " + hour, "%Y-%m-%d %H:%M:%S")
        secs = time.mktime(tmpsecs)

        return secs


    #### CONTROLLERS ####

    # -- CRYPTO controller --
    def crypto_controller(self, controller):
        count = 0
        exch = None

        if controller.upper() == "BINANCE":
            if 'libbinance' not in sys.modules:
                import libbinance
                exch = libbinance.libbinance()

        #if controller.upper() == "BITFINEX":
        #    if 'libbitfinex' not in sys.modules:
        #        import libbitfinex
        #        exch = libbitfinex.libbitfinex()

        if controller.upper() == "BITTREX":
            if 'libbittrex' not in sys.modules:
                import libbittrex
                exch = libbittrex.libbittrex()

        if controller.upper() == "OKEX":
            if 'libokex' not in sys.modules:
                import libokex
                exch = libokex.libokex()

        if controller.upper() == "HUOBI":
            if 'libhuobi' not in sys.modules:
                import libhuobi
                exch = libhuobi.libhuobi()

        exch.debug_mode = self.debug_mode
        exch.init_exchange()

        while True:
            self.get_fecha_hora()
            secs = self.fh['secs']

            # -- get data --
            result = exch.get_exchange()

            if result != -1:
                data = exch.parse_page(result)

                if data != -1:
                    # -- update last_flag --
                    params1 = {'last_flag': 0}
                    params2 = [
                        "last_flag=1",
                        "ticker LIKE '" + exch.controller['preintticker'] + "%'"
                    ]
                    db.generic_update(params1, params2, "prices")

                    if self.debug_mode >= 1:
                        print(exch.controller['name'] + " controller:")
                        for i in data:
                            print(i)
                    db.generic_row_insert(data, "prices")

            # -- calculate pause in seconds and sleep --
            self.get_fecha_hora()

            segundos = 1
            secs = self.fh['sec'] + segundos
            while secs % int(exch.controller['timepace']) != 0:
                segundos += 1
                secs = self.fh['sec'] + segundos

            if self.debug_mode >= 1:
                print("---")
                print(
                "secs. remaining: " + str(segundos) + " for " + exch.controller['name'] + " (count " + str(count) + ")")
                print("---")

            time.sleep(segundos)
            count += 1
            self.get_fecha_hora()

        os._exit(0)

        return


    #### PROCESS MANAGMENT ####

    # -- get launched processes and relaunch if down --
    def get_analyze_process(self, program):
        linesps = []
        linesf = []
        programsmulti = ['allstream']
        new_process_file = []
        count_down = 0
        restart_tickers = []

        # -- get app name --
        tmp = program.split("/")
        app = tmp[-1]

        # -- get process from ps --
        # comando = "ps auwx | grep "+app+" | egrep -v 'grep|vi ' | awk {'print $2 $12'}"
        comando = "ps -eo pid,command | grep " + app + " | egrep -v 'grep|vi'"
        tmpps = commands.getoutput(comando).split("\n")
        #tmpps = subprocess.getoutput(comando).split("\n")

        for i in tmpps:
            if i != "":
                tmp = i.split(" ")
                linesps.append(tmp)

        # -- program not running, then execute it --
        if len(linesps) == 0:
            self.run_program(program)
            return

        if len(linesps) == 1 and linesps[0] == "":
            self.run_program(program)
            return

        # -- remove duplicate process if apply --
        if len(linesps) > 1:
            for i in range(0, len(linesps) - 1):
                kill = 1
                for i in programsmulti:
                    if app.find(i) < 0:
                        kill = 0
                if kill == 1:
                    self.kill_process_by_pid(i[0])

        # -- allstream special checkings --
        if app.find("allstream") >= 0:
            # -- get lines --
            fd = open(self.process_file, "r")
            tmplinesf = fd.read().split("\n")
            fd.close()

            print("LINESF: (" + str(len(tmplinesf)) + ")")
            for i in tmplinesf:
                if i != "":
                    tmp = i.split("\t")
                    linesf.append(tmp)
                    print(tmp)
            print("------------------------")

            truef = []
            controllers = []
            proc_controll = []
            for i in linesf:
                if i[1] not in controllers:
                    controllers.append(i[1])
                    proc_controll.append({'controller': i[1], 'process': 1, 'pids': [i[0]], 'tickers': i[2]})
                else:
                    for n in proc_controll:
                        if n['controller'] == i[1]:
                            n['pids'].append(i[0])
                            n['process'] += 1

            # -- rewrite process file when 1 process per controller and execute if not running --
            print("REMOVING PROCESS FILE " + self.process_file + "...")
            os.remove(self.process_file)
            fp = open(self.process_file, "w")
            for i in proc_controll:
                if i['process'] == 1:
                    running = 0
                    for n in linesps:
                        if n[0] == i['pids'][0]:
                            running = 1

                    if running == 0:
                        self.run_program(program + " -m " + i['controller'])
                    else:
                        process_line = i['pids'][0] + "\t" + i['controller'] + "\t" + i['tickers'] + "\n"
                        fp.write(process_line)
            fp.close()

            # -- when more than 1 process per controller kill all and restart in 1 controller --
            for i in proc_controll:
                if i['process'] > 1:
                    for n in i['pids']:
                        self.kill_process_by_pid(n)
                    print("STARTING: " + program + " -m " + i['controller'] + "...")
                    self.run_program(program + " -m " + i['controller'])

        return


    # -- kill process by pid --
    def kill_process_by_pid(self, pid):
        comando = "kill -9 " + pid
        commands.getoutput(comando)
        #subprocess.getoutput(comando)

        return


    # -- kill all process and delete process file --
    def kill_all_process(self):
        fp = open(self.process_file, "wb")
        fp.close()

        psprogram = self.launcher.split("/")[-1]
        comando = "ps auwx | grep '" + psprogram + "' | egrep -v 'grep|vi ' | awk {'print $2'} | sort"
        if self.debug_mode > 1:
            print(comando)
        linesps = commands.getoutput(comando).split("\n")
        #linesps = subprocess.getoutput(comando).split("\n")

        if len(linesps) > 0:
            for i in range(0, len(linesps) - 1):
                if linesps[i] != "":
                    comando = "kill -9 " + linesps[i]
                    if self.debug_mode > 1:
                        print(comando)
                    commands.getoutput(comando)
                    #subprocess.getoutput(comando)

        return


    # -- look for programs down --
    def get_process_program(self, program):
        got_program = 0

        exec_command = program.split("/")[-1]
        comando = "ps auwx | grep '" + exec_command + "' | egrep -v 'grep|vi ' | sort"

        if self.debug_mode > 1:
            print(comando)
        lines = commands.getoutput(comando).split("\n")
        #lines = subprocess.getoutput(comando).split("\n")

        for i in lines:
            if i.find(exec_command) >= 0:
                got_program = 1

        return got_program


    # -- exec a program --
    def run_program(self, program):
        comando = program + " &"
        if self.debug_mode > 1:
            print(comando)
        os.system(comando)

        return


