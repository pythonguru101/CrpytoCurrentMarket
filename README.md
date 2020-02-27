# README #

The program Allstream makes possible to download financial data from different sources at the same time using threads.
This programs it is an excellent base for developing trading bots or financial analysis data software.

### Installation ###

* Create a new fresh mysql database called ccmarket.
* pip install -r requirements.txt
* mysql (-h host -u'user' -p'password') ccmarket < schema-ccmarket.sql
* Copy crontab_backup.txt content to crontab with crontab -e

### Make program working ###

* First of all you have to add all exchange markets into the program:
  ./market-conversor.py -a -m (BINANCE|BITTREX|HUOBI|OKEX)

* Once markets on database you simply run the downloader for all markets:
  ./allstream.py -m (BINANCE|BITTREX|HUOBI|OKEX)

* The database will be filled with market values from now.

* To start the website GUI:
  cd website
  ./gunicorn-start.sh

* Go to server IP, if local machine: http://127.0.0.1:8080

* All done.

### Author ###

pythonguru101@gmail.com
