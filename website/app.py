#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import time
import os
import commands
# import subprocess
import base64
import csv
import re
import json
import libdb_mysql_web
import decimal
from operator import itemgetter
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from datetime import datetime

app = Flask(__name__)

db = libdb_mysql_web.libdb_mysql()


##########################################################################
### MAIN WEB PAGE FUNCTIONS

def chart(coin_name):
    price_list = []
    item = []
    condition = "ticker='"+coin_name+"'"
    capitalizations = db.generic_select([condition], "capitalization")
    for i in capitalizations:
        item.append(i['secs'])
        item.append(i['last'])
        price_list.append(item)
        item = []
    return price_list


@app.route('/coinmarketcap.html', methods=['GET'])
def get_cmc():
    price_in_usd = 0
    btc = 0
    eth = 0
    price_in_btc = 0
    price_in_eth = 0
    market_cap = 0
    volume24 = 0
    secs_list = []
    selected_coin_prefix = 'CM-'
    coin_sel = 'CM-BTC'

    capitalizations = db.generic_select(["last_flag=1"], "capitalization")
    for item in capitalizations:
        secs_list.append(item['secs'])

    latest_secs = max(secs_list)

    for item in capitalizations:
        if item['secs'] == latest_secs and "CM-" in item['ticker']:
            selected_coin_prefix = 'CM-'
        if item['secs'] == latest_secs and "MK-" in item['ticker']:
            selected_coin_prefix = 'MK-'

    if request.args.get('coin'):
        coin_sel = selected_coin_prefix + str(request.args.get('coin'))

    price = chart(coin_sel)

    for item in capitalizations:
        if item['secs'] == latest_secs and item['ticker'] == coin_sel:
            market_cap = item['market_cap']
            market_cap = format(market_cap, '.1f')
            volume24 = item['volume']
        if item['secs'] == latest_secs and item['ticker'] == selected_coin_prefix + "BTC":
            btc = item['last']
        if item['secs'] == latest_secs and item['ticker'] == selected_coin_prefix + "ETH":
            eth = item['last']

    day_range = []
    for item in capitalizations:
        if 0 <= latest_secs - item['secs'] \
                and latest_secs - item['secs'] <= 24 * 60 * 60 \
                and item['ticker'] == coin_sel:
            day_range.append(item['last'])

    for item in capitalizations:
        if item['secs'] == latest_secs and item['ticker'] == coin_sel:
            price_in_usd = item['last']
        if btc != 0:
            price_in_btc = '%.12f' % (price_in_usd / btc)
        if eth != 0:
            price_in_eth = '%.12f' % (price_in_usd / eth)

    range_1d = []
    for item in capitalizations:
        if 0 <= latest_secs - item['secs'] \
                and latest_secs - item['secs'] <= 24 * 60 * 60 \
                and item['ticker'] == coin_sel:
            range_1d.append(item['last'])

    range_7d = []
    for item in capitalizations:
        if 0 <= latest_secs - item['secs'] \
                and latest_secs - item['secs'] <= 7 * 24 * 60 * 60 \
                and item['ticker'] == coin_sel:
            range_7d.append(item['last'])

    range_52w = []
    for item in capitalizations:
        if 0 <= latest_secs - item['secs'] \
                and latest_secs - item['secs'] <= 52 * 7 * 24 * 60 * 60 \
                and item['ticker'] == coin_sel:
            range_52w.append(item['last'])

    vol_list_52w = []
    average_vol_52w = 0
    for item in capitalizations:
        if 0 <= latest_secs - item['secs'] \
                and latest_secs - item['secs'] <= 52 * 7 * 24 * 60 * 60 \
                and item['ticker'] == coin_sel:
            vol_list_52w.append(item['volume'])
    if len(vol_list_52w) != 0:
        average_vol_52w = sum(vol_list_52w) / len(vol_list_52w)

    whole_range = []
    for item in capitalizations:
        if item['ticker'] == coin_sel:
            whole_range.append(item['last'])

    secs_7d_last = 0
    basic_secs_7d = max(secs_list) - 7 * 24 * 60 * 60
    secs_7d = min(secs_list, key=lambda x: abs(x - basic_secs_7d))
    for item in capitalizations:
        if item['secs'] == secs_7d and item['ticker'] == coin_sel:
            secs_7d_last = item['last']

    secs_1m_last = 0
    basic_secs_1m = max(secs_list) - 30 * 24 * 60 * 60
    secs_1m = min(secs_list, key=lambda x: abs(x - basic_secs_1m))
    for item in capitalizations:
        if item['secs'] == secs_1m and item['ticker'] == coin_sel:
            secs_1m_last = item['last']

    secs_6m_last = 0
    basic_secs_6m = max(secs_list) - 6 * 30 * 24 * 60 * 60
    secs_6m = min(secs_list, key=lambda x: abs(x - basic_secs_6m))
    for item in capitalizations:
        if item['secs'] == secs_6m and item['ticker'] == coin_sel:
            secs_6m_last = item['last']

    ticker_list = []
    for item in capitalizations:
        if item['secs'] == latest_secs:
            item['market_cap'] = format(item['market_cap'], '.1f')
            item['ticker'] = item['ticker'][3:]
            ticker_list.append(item)

    alldata = {'market_cap': market_cap,
               'day_range_max': max(day_range),
               'day_range_min': min(day_range),
               'volume24': volume24,
               'circulating_supply': '-',
               'price_in_usd': price_in_usd,
               'price_in_btc': price_in_btc,
               'price_in_eth': price_in_eth,
               'range_max_1d': max(range_1d),
               'range_min_1d': min(range_1d),
               'range_max_7d': max(range_7d),
               'range_min_7d': min(range_7d),
               'range_max_52w': max(range_52w),
               'range_min_52w': min(range_52w),
               'average_vol_52w': average_vol_52w,
               'all_time_high': max(whole_range),
               'percent_from_ath': max(whole_range) - price_in_usd,
               'cap_in_btc': float(market_cap) / float(btc),
               'pro_7d': (secs_7d_last - price_in_usd) / price_in_usd * 100,
               'pro_1m': (secs_1m_last - price_in_usd) / price_in_usd * 100,
               'pro_6m': (secs_6m_last - price_in_usd) / price_in_usd * 100,
               'ticker_list': ticker_list,
               'coin_sel': coin_sel[3:],
               'updated': datetime.fromtimestamp(latest_secs).strftime("%d/%m/%Y %H:%M:%S"),
               'price_list': price
               }

    return render_template("coinmarketcap.html", data=alldata)


@app.route('/download.html', methods=['POST'])
def download():
    values = {}
    ticker_list = []
    csv_list = []
    option = None

    controller = request.form.get('controller')

    tmpsecs = time.strptime(request.form.get('dini') + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    ini_secs = int(time.mktime(tmpsecs))
    tmpsecs = time.strptime(request.form.get('dend') + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    end_secs = int(time.mktime(tmpsecs))

    if request.form.get('option').lower() == "prices":
        option = "last"
    if request.form.get('option').lower() == "dollars":
        option = "dollars"
    if request.form.get('option').lower() == "volume":
        option = "volume"

    # -- get involved tickers --
    values['time'] = []
    params = [
        "controller='" + controller + "'",
        "active=1",
        "ORDER BY localticker"
    ]
    tickers = db.generic_select(params, "tickers")

    ticker_list.append('time')
    for i in tickers:
        ticker_list.append(i['remoteticker'])

    for i in tickers:
        data_table = "prices"
        if controller == "COINMARKETCAP":
            data_table = "capitalization"
        params = [
            "SELECT secs, " + option,
            "ticker='" + i['localticker'] + "'",
            "secs>=" + str(ini_secs),
            "secs<=" + str(end_secs),
            "ORDER BY secs"
        ]
        data = db.generic_select(params, data_table)

        if len(data) > 0:
            if values['time'] == []:
                for n in data:
                    values['time'].append(n['secs'])
            values[i['remoteticker']] = []
            for n in data:
                if option == "last":
                    values[i['remoteticker']].append(n['last'])
                if option == "dollars":
                    values[i['remoteticker']].append(n['dollars'])
                if option == "volume":
                    values[i['remoteticker']].append(n['dayvol'])

                # -- fill data for CSV --
                for i in range(0, len(values['time'])):
                    tmp = {}
                    for n in values.keys():
                        if n == "time":
                            tmpdate = time.localtime(values[n][i])
                            tmp[n] = time.strftime("%Y-%m-%d %H:%M:%S", tmpdate)
                    for n in values.keys():
                        if n <> "time":
                            try:
                                tmp[n] = ('%16.8f' % values[n][i]).strip()
                            except:
                                tmp[n] = ('%16.8f' % values[n][-1]).strip()
                    csv_list.append(tmp)

                # -- write to CSV file on /tmp --
                if option == "last":
                    option = "prices"

                dini = re.sub("-", "", request.form.get('dini'))
                dend = re.sub("-", "", request.form.get('dend'))

                csv_file = controller + "_" + dini + "_" + dend + "_" + option + ".csv"

                fp = open("/tmp/" + csv_file, 'wb')
                writer = csv.DictWriter(fp, fieldnames=ticker_list, extrasaction='ignore', delimiter=',',
                                        quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for i in csv_list:
                    writer.writerow(i)
                fp.close()

                return send_file("/tmp/" + csv_file, mimetype="text/csv", attachment_filename=csv_file,
                                 as_attachment=True)


@app.route('/csv-download.html', methods=['GET'])
def csv_download():
    controllers = []

    # -- get data --
    controllers = db.generic_select([], "controllers")
    today = time.strftime("%Y-%m-%d", time.localtime())
    alldata = {'controllers': controllers, 'date': today}

    return render_template("csv-download.html", data=alldata)


@app.route('/save-bot-config.html', methods=['POST'])
def savebotconfig():
    bot_config = {
        'volume': 0.00,
    }

    # -- process arguments --
    if request.method == 'POST':
        volume = request.form['volume']

        if volume != "":
            bot_config['volume'] = float(volume)

        params1 = bot_config
        params2 = ["id=1"]
        db.generic_update(params1, params2, "bot_config")

        # -- reinitialize allstream --
        db.path = os.getcwd() + "/"
        db.stopper = db.path + "../sd-allstream.py"

        print("Stopping allstream...")
        os.system(db.stopper + " &")
        time.sleep(1)

    return redirect(url_for('configbot'))


@app.route('/config-bot.html', methods=['GET'])
def configbot():
    alldata = {}

    tmp = db.generic_select([], "bot_config")
    bot_config = tmp[0]

    bot_config['vol10'] = ""
    if bot_config['volume'] == 10:
        bot_config['vol10'] = " checked"
    bot_config['vol25'] = ""
    if bot_config['volume'] == 25:
        bot_config['vol25'] = " checked"
    bot_config['vol50'] = ""
    if bot_config['volume'] == 50:
        bot_config['vol50'] = " checked"
    bot_config['vol75'] = ""
    if bot_config['volume'] == 75:
        bot_config['vol75'] = " checked"
    bot_config['vol100'] = ""
    if bot_config['volume'] == 100:
        bot_config['vol100'] = " checked"

    alldata = {'bot_config': bot_config}

    return render_template("config-bot.html", data=alldata)


@app.route('/csv-operations.html', methods=['GET'])
def csv_operations():
    args_filter = 1
    argums = {
        'start_date': "",
        'end_date': "",
        'ticker': "",
        'op_type': "",
        'status_type': "",
    }

    # -- get arguments --
    argums['start_date'] = request.args.get('start_date')
    argums['end_date'] = request.args.get('end_date')

    argums['ticker'] = request.args.get('ticker')
    if argums['ticker'] is not None:
        argums['ticker'] = "BI-" + request.args.get('ticker')

    argums['op_type'] = request.args.get('op_type')
    argums['status_type'] = request.args.get('status_type')

    if argums['start_date'] is None \
            and argums['end_date'] is None \
            and argums['ticker'] is None \
            and argums['op_type'] is None \
            and argums['status_type'] is None:
        args_filter = 0

    # -- get data --
    params = []

    params.append("ORDER BY timestamp DESC")

    operations = db.generic_select(params, "operations")
    if len(operations) != []:
        for i in range(0, len(operations)):
            operations[i]['price1'] = ('%16.8f' % operations[i]['price1']).strip()
            operations[i]['price2'] = ('%16.8f' % operations[i]['price2']).strip()

    # -- make csv file --
    # return render_template("csv-operations.html", data=alldata)
    csv_data = []
    csv_file = "operations.csv"
    titles = ['Time', 'Ticker', 'Operation', 'Price', 'Status']
    status = ['Success', 'Failed', 'No Funds']
    for i in operations:
        txt_status = status[i['end_status']]

        tmp = {
            'Time': str(i['pdate']) + " " + str(i['ptime']),
            'Ticker': i['ticker'],
            'Operation': i['operation'],
            'Price': i['price'],
            'Status': txt_status
        }
        csv_data.append(tmp)

    fp = open(csv_file, 'wb')
    writer = csv.DictWriter(fp, fieldnames=titles, extrasaction='ignore', delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    writer.writeheader()
    for i in csv_data:
        writer.writerow(i)
    fp.close()

    return send_file(csv_file, mimetype="text/csv", attachment_filename=csv_file, as_attachment=True)


@app.route('/operation-review.html', methods=['GET'])
def op_review():
    op_id = request.args.get('id')

    params = [
        "op_id=" + str(op_id),
        "ORDER BY status"
    ]
    alldata = db.generic_select(params, "op_tracking")

    return render_template("operation-review.html", data=alldata)


@app.route('/operations.html', methods=['GET'])
def operations():
    alldata = []
    args_filter = 1
    argums = {
        'start_date': "",
        'end_date': "",
        'ticker': "",
        'op_type': "",
        'status_type': "",
    }

    # -- get arguments --
    tmp = request.args.get('page')
    curr_page = 1
    if tmp != "" \
            and tmp is not None:
        curr_page = int(tmp)
        if curr_page < 1:
            curr_page = 1

    argums['start_date'] = request.args.get('start_date')
    argums['end_date'] = request.args.get('end_date')

    argums['ticker'] = request.args.get('ticker')
    if argums['ticker'] is not None:
        argums['ticker'] = "BI-" + request.args.get('ticker')

    argums['op_type'] = request.args.get('op_type')
    argums['status_type'] = request.args.get('status_type')

    if argums['start_date'] is None \
            and argums['end_date'] is None \
            and argums['ticker'] is None \
            and argums['op_type'] is None \
            and argums['status_type'] is None:
        args_filter = 0

    # -- get all filter data --
    params = ["SELECT DISTINCT(ticker)"]
    tickers = db.generic_select(params, "operations")

    show_tickers = [{'ticker': 'All', 'selected': ""}]
    for i in tickers:
        if argums['ticker'] == i['ticker']:
            tmp = {'ticker': i['ticker'][3:], 'selected': " selected"}
        else:
            tmp = {'ticker': i['ticker'][3:], 'selected': ""}
        show_tickers.append(tmp)

    op_types = []
    for i in ['All', 'Buy', 'Sell']:
        if argums['op_type'] == i:
            tmp = {'op_type': i, 'selected': " selected"}
        else:
            tmp = {'op_type': i, 'selected': ""}
        op_types.append(tmp)

    status_types = []
    for i in ['All', 'Success', 'Failed']:
        if argums['status_type'] == i:
            tmp = {'status_type': i, 'selected': " selected"}
        else:
            tmp = {'status_type': i, 'selected': ""}
        status_types.append(tmp)

    # -- make filter query --
    params = []

    if argums['start_date'] is not None \
            and argums['start_date'] != "":
        start_date = time.strftime("%Y-%m-%d", time.strptime(argums['start_date'], "%d-%b-%Y"))
        params.append("pdate>='" + start_date + "'")
    if argums['end_date'] is not None \
            and argums['end_date'] != "":
        end_date = time.strftime("%Y-%m-%d", time.strptime(argums['end_date'], "%d-%b-%Y"))
        params.append("pdate<='" + end_date + "'")
    if argums['ticker'] is not None \
            and argums['ticker'] != "BI-":
        params.append("ticker='" + argums['ticker'] + "'")
    if argums['op_type'] is not None:
        if argums['op_type'] == "Buy":
            params.append("operation='B'")
        if argums['op_type'] == "Sell":
            params.append("operation='S'")
    if argums['status_type'] is not None:
        if argums['status_type'] == "Success":
            params.append("end_status=0")
        if argums['status_type'] == "Failed":
            params.append("end_status=1")
        if argums['status_type'] == "No Funds":
            params.append("end_status=2")

    params.append("ORDER BY timestamp DESC")

    operations = db.generic_select(params, "operations")

    # -- correct date arguments --
    if argums['start_date'] is None:
        argums['start_date'] = ""
    if argums['end_date'] is None:
        argums['end_date'] = ""

    # -- compose operations for page --
    if len(operations):
        for i in range(0, len(operations)):
            operations[i]['price'] = ('%16.8f' % operations[i]['price']).strip()
            operations[i]['status'] = "Success"
            if operations[i]['end_status'] == 1:
                operations[i]['status'] = "Failed"
            if operations[i]['end_status'] == 2:
                operations[i]['status'] = "No Funds"

    # -- compose paginator --
    pages_url = "/operations.html"
    if request.query_string != "":
        end = request.query_string.find("&page=")
        pages_url += "?" + request.query_string[0:end]
    print("PAGES_URL:")
    print(pages_url)
    page_list = db.paginator(operations, curr_page, 25, pages_url)

    alldata = {'operations': page_list['rows'], 'pages': page_list['pages'], 'argums': argums, 'tickers': show_tickers,
               'op_types': op_types, 'status_types': status_types, 'args_filter': args_filter}

    return render_template("operations.html", data=alldata)


@app.route('/stop.html')
def stop_bot():
    # if not session.get('logged_in'):
    #	return redirect(url_for('login'))

    comando = "ps auwx | grep -i 'python' | grep -i 'botcommand' | grep -v 'grep' | awk {'print $2'}"
    result = commands.getoutput(comando).split("\n")
    # result = subprocess.getoutput(comando).split("\n")
    for i in result:
        if len(i) > 1:
            comando = "kill -9 " + str(i)
            os.system(comando)

    return redirect(url_for('bot_control'))


@app.route('/run.html')
def run_bot():
    # if not session.get('logged_in'):
    #	return redirect(url_for('login'))

    # -- start bot --
    comando = "cd ../ && " + db.path + "botcommand.py &"
    print("COMANDO:")
    print(comando)
    os.system(comando)

    return redirect(url_for('bot_control'))


@app.route('/bot-control.html')
def bot_control():
    log_text = ""
    running_state = 0
    stopping_state = 0
    log_file = db.path + "bot_log.log"

    # -- get current state --
    comando = "ps auwx | grep -i 'python' | grep -i 'botcommand' | grep -v 'vi ' | grep -v 'grep'"
    lines = commands.getoutput(comando).split("\n")
    # lines = subprocess.getoutput(comando).split("\n")

    if len(lines) > 0:
        if len(lines[0]) > 1:
            running_state = 1

    if os.path.isfile(db.path + "stop_bot.ctl"):
        stopping_state = 1

    print("RUNNING:")
    print(running_state)
    print("STOPPING:")
    print(stopping_state)
    print("---------------------------")

    # -- if bot not running prepare or create log file for reading --
    if running_state == 0:
        if not os.path.isfile(log_file):
            fp = open(log_file, "w")
            fp.write("")
            fp.close()

    # -- if bot is running, get log file and check stopping --
    # if running_state == 1:
    fp = open(log_file, "r")
    log_text = fp.read().split("\n")
    fp.close()

    alldata = {'running_state': running_state, 'log_text': log_text, 'path': db.path, 'stopping_state': stopping_state}

    return render_template("bot-control.html", data=alldata)


@app.route('/save-ticker.html', methods=['GET'])
def save_ticker():
    active = 0
    active_selected = request.args.getlist('active')
    check_selected = bool(active_selected)

    if check_selected == True:
        active = 1

    # -- update data --
    params1 = {
        'active': active,
        'name': request.args.get('name'),
        'localticker': request.args.get('localticker'),
        'remoteticker': request.args.get('remoteticker'),
        'controller': request.args.get('controller')
    }
    params2 = ["id=" + str(request.args.get('id'))]
    db.generic_update(params1, params2, "tickers_tmp")

    return redirect(url_for('setup'))


@app.route('/edit-ticker.html', methods=['GET'])
def edit_ticker():
    ticker_id = request.args.get('ticker')
    controllers = []

    # -- get arguments --
    controller = request.args.get('controller')
    if controller is None:
        controller = ""

    # -- get data --
    params = ["id=" + str(ticker_id)]
    ticker = db.generic_select(params, "tickers_tmp")[0]
    if ticker['active'] == 1:
        ticker['active'] = " checked"
    tmp = db.generic_select([], "controllers")

    # -- add default for controller list --
    for i in tmp:
        if i['controller'] == ticker['controller']:
            controllers.append({'controller': i['controller'], 'selected': " selected"})
        else:
            controllers.append({'controller': i['controller'], 'selected': ""})

    alldata = {'controllers': controllers, 'ticker': ticker}

    return render_template("edit-ticker.html", data=alldata)


@app.route('/get-controller-ids.html', methods=['GET'])
def get_controller_ids():
    ticker_ids = []
    controller = ""
    controller = request.args.get('controller')
    search = request.args.get('search')

    ticker_ids = db.get_ticker_id_search(controller, search)

    alldata = {'tickers': ticker_ids}

    return jsonify(alldata)


@app.route('/update-controller.html', methods=['GET'])
def update_controller():
    controller = str(request.args.get('controller'))
    search = str(request.args.get('search'))
    arg_active = str(request.args.get('active'))
    referer = ""

    if controller == "None":
        controller = ""
    if search == "None":
        search = ""

    db.update_controller_active(controller, search, arg_active)

    return redirect(url_for('setup', controller=controller, search=search))


@app.route('/update-list.html')
def update_list():
    ticker_id = ""
    active = 0

    ticker_id = request.args.get('ticker')
    arg_active = int(request.args.get('active'))

    params1 = {'active': arg_active}
    params2 = ["id=" + str(ticker_id)]
    db.generic_update(params1, params2, "tickers_tmp")

    return redirect(url_for('setup'))


@app.route('/apply.html', methods=['GET'])
def apply_changes():
    referer = None
    controller = str(request.args.get('controller'))
    search = str(request.args.get('search'))
    if controller == "None":
        controller = ""
    if search == "None":
        search = ""

    return_function = "setup"
    db.generic_delete([], "tickers")
    db.fill_tickers_tmp("tickers_tmp", "tickers")

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    if referer == "config-exchanges.html":
        return_function = "setup_exchanges"
    if referer == "config-times.html":
        return_function = "setup_times"
    if referer == "config-fees.html":
        return_function = "setup_fees"
    if referer == "config-keys.html":
        return_function = "setup_keys"

    # -- reinitialize allstream --
    db.path = os.getcwd() + "/../"
    db.launcher = db.path + "allstream.py"
    # db.histo_launcher = db.path+"allhistorical.py"
    db.stopper = db.path + "sd-allstream.py"

    print("Stopping allstream and allhistorical...")
    os.system(db.stopper + " &")
    time.sleep(1)
    # print("Relaunching allstream...")
    # os.system(db.launcher+" &")
    # print("Relaunching allhistorical...")
    # os.system(db.histo_launcher+" &")

    return redirect(url_for(return_function, message='saved', controller=controller, search=search))


@app.route('/save-keys.html', methods=['GET'])
def save_keys():
    referer = ""

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    controller = str(request.args.get('controller'))
    key = str(request.args.get('key'))
    secret = str(request.args.get('secret'))
    passphrase = str(request.args.get('passphrase'))

    params1 = {
        'api_key': key,
        'api_secret': secret,
        'passphrase': passphrase
    }
    params2 = ["controller='" + controller + "'"]
    db.generic_update(params1, params2, "controllers")

    return redirect(url_for('setup_keys', message='saved'))


@app.route('/save-fees.html', methods=['GET'])
def save_fees():
    referer = ""

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    controller = str(request.args.get('controller'))
    fee = str(request.args.get('fee'))

    params1 = {'fee': fee}
    params2 = ["controller='" + controller + "'"]
    db.generic_update(params1, params2, "controllers")

    return redirect(url_for('setup_fees', message='saved'))


@app.route('/save-times.html', methods=['GET'])
def save_times():
    referer = ""

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    controller = str(request.args.get('controller'))
    timepace = str(request.args.get('timepace'))

    params1 = {'timepace': timepace}
    params2 = ["controller='" + controller + "'"]
    db.generic_update(params1, params2, "controllers")

    return redirect(url_for('setup_times', message='saved'))


@app.route('/config-keys.html')
def setup_keys():
    alldata = []
    modified = 0
    referer = ""
    finished = 0

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    # -- get arguments --
    tmp = str(request.args.get('message'))
    if tmp == "saved":
        finished = 1

    controllers = db.generic_select([], "controllers")

    # -- conditions for modified --
    if referer.find("save-keys.html") == 0:
        modified = 1

    # -- create data representation for page --
    alldata = {'controllers': controllers, 'modified': modified, 'finished': finished}

    return render_template("config-keys.html", data=alldata)


@app.route('/config-fees.html')
def setup_fees():
    alldata = []
    modified = 0
    referer = ""
    finished = 0

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    # -- get arguments --
    tmp = str(request.args.get('message'))
    if tmp == "saved":
        finished = 1

    controllers = db.generic_select([], "controllers")

    # -- conditions for modified --
    if referer.find("save-fees.html") == 0:
        modified = 1

    # -- create data representation for page --
    alldata = {'controllers': controllers, 'modified': modified, 'finished': finished}

    return render_template("config-fees.html", data=alldata)


@app.route('/config-times.html')
def setup_times():
    alldata = []
    modified = 0
    referer = ""
    finished = 0

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    # -- get arguments --
    tmp = str(request.args.get('message'))
    if tmp == "saved":
        finished = 1

    controllers = db.generic_select([], "controllers")

    # -- conditions for modified --
    if referer.find("save-times.html") == 0:
        modified = 1

    # -- create data representation for page --
    alldata = {'controllers': controllers, 'modified': modified, 'finished': finished}

    return render_template("config-times.html", data=alldata)


@app.route('/config-tickers.html', methods=['GET'])
def setup():
    alldata = []
    modified = 0
    referer = ""
    finished = 0

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    # -- get arguments --
    controller = str(request.args.get('controller'))
    search = str(request.args.get('search'))
    if controller == "None":
        controller = ""
    if search == "None":
        search = ""

    tmp = str(request.args.get('message'))
    if tmp == "saved":
        finished = 1

    # -- delete tickers_tmp, refill, get controllers and tickers --
    if referer.find("config-tickers.html") < 0 \
            and referer.find("edit-ticker.html") < 0:
        db.generic_delete([], "tickers_tmp")
        db.fill_tickers_tmp("tickers", "tickers_tmp")

    # -- get controllers --
    controllers = db.generic_select([], "controllers")
    if controller == "":
        controller = controllers[0]['controller']

    # -- if there is a search argument go to search --
    # if search != "":
    #	return redirect(url_for('search', controller=controller, search=search))

    # -- load data --
    for i in range(0, len(controllers)):
        if controllers[i]['controller'] == controller:
            controllers[i]['selected'] = " selected"
        else:
            controllers[i]['selected'] = ""

    # -- get tickers --
    tickers = db.get_search_tickers(-1, "tickers_tmp", controller, search)
    orig_tickers = db.get_search_tickers(-1, "tickers", controller, search)

    # -- conditions for modified --
    if referer.find("save-ticker.html") == 0 \
            or tickers != orig_tickers:
        modified = 1

    alldata = {'search': search, 'controllers': controllers, 'controller': controller, 'modified': modified,
               'finished': finished, 'settings': {'total': 0, 'selected': 0, 'allsel': ""}, 'tickers': []}

    # -- create data representation for page --
    numtickers = 0
    seltickers = 0
    for i in range(0, len(tickers)):
        tickers[i]['checked'] = ""
        if tickers[i]['active'] == 1:
            tickers[i]['checked'] = " checked"
            seltickers += 1
        numtickers += 1

    alldata['tickers'] = tickers
    alldata['settings']['total'] = numtickers
    alldata['settings']['selected'] = seltickers
    if alldata['settings']['total'] == alldata['settings']['selected']:
        alldata['settings']['allsel'] = " checked"

    return render_template("config-tickers.html", data=alldata)


@app.route('/config-exchanges.html')
def setup_exchanges():
    alldata = []
    modified = 0
    referer = ""
    finished = 0

    # -- get origin page --
    if "HTTP_REFERER" in request.environ.keys():
        referer = request.environ['HTTP_REFERER'].split("/")[-1]

    # -- get arguments --
    tmp = str(request.args.get('message'))
    if tmp == "saved":
        finished = 1

    # -- delete tickers_tmp, refill, get controllers and tickers --
    if referer == "index.html" or referer == "":
        db.generic_delete([], "tickers_tmp")
        db.fill_tickers_tmp("tickers", "tickers_tmp")

    controllers = db.generic_select([], "controllers")
    params = ["ORDER BY controller, remoteticker"]
    tickers = db.generic_select(params, "tickers_tmp")
    orig_tickers = db.generic_select(params, "tickers")

    # -- conditions for modified --
    if referer == "save-ticker.html" \
            or tickers != orig_tickers:
        modified = 1

    # -- create data representation for page --
    for i in range(0, len(controllers)):
        active = ""
        activated = "0"
        for n in tickers:
            if n['controller'] == controllers[i]['controller']:
                if str(n['active']) == "1":
                    active = " checked"
                    activated = "1"

        alldata.append(
            {'controller': controllers[i]['controller'], 'active': active, 'activated': activated, 'modified': modified,
             'finished': finished})

    return render_template("config-exchanges.html", data=alldata)


@app.route('/view-log.html')
def view_log():
    alldata = {}

    # -- get arguments --
    secs = str(request.args.get('secs'))

    # -- get listing --
    params = ["secs=" + secs]
    listing = db.generic_select(params, "opportunities")

    # -- date hour --
    tmpdate = time.localtime(listing[0]['secs'])
    log_date = time.strftime("%d-%m-%Y %H:%M:%S", tmpdate)

    for i in range(0, len(listing)):
        listing[i]['operation1'] = "B"
        listing[i]['operation2'] = "S"
        if listing[i]['op_type'] == "S-B":
            listing[i]['operation1'] = "S"
            listing[i]['operation2'] = "B"

        listing[i]['ticker1'] = listing[i]['ticker1'][3:]
        listing[i]['ticker2'] = listing[i]['ticker2'][3:]
        listing[i]['price1'] = '%16.8f' % listing[i]['price1']
        listing[i]['price2'] = '%16.8f' % listing[i]['price2']
        listing[i]['pot_profit'] = '%16.8f' % listing[i]['pot_profit']

    listing = sorted(listing, key=itemgetter("pot_profit"))
    listing.reverse()

    alldata = {'datehour': log_date, 'log': listing}

    return render_template("view-log.html", data=alldata)


@app.route('/index.html')
@app.route('/screener.html')
@app.route('/')
def screener():
    data = []
    prices = []
    lastsecs = int(time.time())
    controller = None

    # -- get controller --
    controller_sel = str(request.args.get('controller'))

    # -- get controllers and tickers --
    controllers = db.generic_select([], "controllers")

    if controller_sel == "None":
        controller = controllers[0]

    for i in range(0, len(controllers)):
        if controllers[i]['controller'] == controller_sel:
            controller = controllers[i]
            controllers[i]['selected'] = " selected"
        else:
            controllers[i]['selected'] = ""

    params = [
        "controller='" + controller['controller'] + "'",
        "active=1",
        "ORDER BY localticker"
    ]
    tickers = db.generic_select(params, "tickers")

    params = [
        "last_flag=1",
        "ticker LIKE '" + controller['preintticker'] + "%'"
    ]
    prices_values = db.generic_select(params, "prices")

    # -- create data representation for page --
    for i in prices_values:
        for n in tickers:
            if i['ticker'] == n['localticker']:
                name = n['name']

        # -- add to list --
        secsdiff = lastsecs - i['secs']
        if secsdiff < 3600:
            updated = "Recently"
        else:
            hours = int(secsdiff / 3600)
            updated = "More than " + str(hours) + " hours"

        last = i['last']
        volume = i['dayvol']

        price = {
            'name': name,
            'localticker': i['ticker'],
            'ticker': i['ticker'][3:],
            'last': format(last, 'f'),
            'volume': volume,
            'updated': updated
        }
        prices.append(price)

    data.append({'controller': controller, 'prices': prices})

    # -- create last date and group all data for template --
    tmpfecha = time.localtime(lastsecs)
    fecha = time.strftime("%Y-%m-%d %H:%M:%S", tmpfecha)

    alldata = {'last_updated': fecha, 'controllers': controllers, 'controller': controller['controller'], 'data': data}

    return render_template("screener.html", data=alldata)


#############################################################################
## MAIN

# db = libdb_mysql.libdb_mysql()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
