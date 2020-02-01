#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import re
import time
import csv

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload

import libdb_mysql


db = libdb_mysql.libdb_mysql()


exchanges = ['BINANCE', 'BITTREX', 'HUOBI', 'OKEX']
csv_files = []


# -- make CSV files --
for i in exchanges:
	print("Creating CSV for: "+i)
	# -- get CSV --
	values = {}
	ticker_list = []
	csv_list = []

	#controller = argums['exchange']
	controller = i


	# -- calculate times --
	end_secs = int(time.time())
	day = int(time.strftime("%d", time.localtime(end_secs)))
	last_day = "01"
	if day == 1:
		last_day = "15"
	ini_secs = end_secs - 1296000
	tmpinidate = time.strftime("%Y-%m-", time.localtime(ini_secs))+last_day
	tmpsecs = time.strptime(tmpinidate+" 00:00:00", "%Y-%m-%d %H:%M:%S")
	ini_secs = time.mktime(tmpsecs)

	# -- get involved tickers --
	values['time'] = []
	params = [
		"controller='"+controller+"'",
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
			"SELECT secs, last",
			"ticker='"+i['remoteticker']+"'",
			"secs>="+str(ini_secs),
			"secs<="+str(end_secs),
			"ORDER BY secs"
		]
		data = db.generic_select(params, data_table)

		if len(data) > 0:
			if values['time'] == []:
				for n in data:
					values['time'].append(n['secs'])
			values[i['remoteticker']] = []
			#for n in data:
			#	if option == "last":
			values[i['remoteticker']].append(n['last'])
			#	if option == "dollars":
			#		values[i['remoteticker']].append(n['dollars'])
			#	if option == "volume":
			#		values[i['remoteticker']].append(n['dayvol'])

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
	#if option == "last":
	option = "prices"

	dini = re.sub("-", "", time.strftime("%Y-%m-%d", time.localtime(ini_secs)))
	dend = re.sub("-", "", time.strftime("%Y-%m-%d", time.localtime(end_secs)))

	csv_file = controller+"_"+dini+"_"+dend+"_"+option+".csv"

	fp = open(csv_file, 'wb')
	writer = csv.DictWriter(fp, fieldnames=ticker_list, extrasaction='ignore', delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
	writer.writeheader()
	for i in csv_list:
		writer.writerow(i)
	fp.close()

	csv_files.append(csv_file)


# -- upload to Google Drive --
print("UPLOADING CSV FILES:")
print(csv_files)

#SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
	with open('token.pickle', 'rb') as token:
		creds = pickle.load(token)
# -- If there are no (valid) credentials available, let the user log in --
if not creds or not creds.valid:
	if creds and creds.expired and creds.refresh_token:
		creds.refresh(Request())
	else:
		flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
		creds = flow.run_local_server(port=0)
	# -- Save the credentials for the next run --
	with open('token.pickle', 'wb') as token:
		pickle.dump(creds, token)

drive = build('drive', 'v3', credentials=creds)


# -- upload files --
for i in csv_files:
	print("Uploading "+i+" to Google Drive...")
	file_metadata = {
		'name': i,
		'mimeType': 'application/vnd.google-apps.spreadsheet'
	}
	media = MediaFileUpload(i, mimetype='text/csv')
	csv_file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
	print ('File ID: %s' % csv_file.get('id'))


# -- delete CSV files --
for i in csv_files:
	os.remove(i)

