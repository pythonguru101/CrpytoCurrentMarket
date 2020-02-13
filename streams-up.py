#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import libmultifeed

mtf = libmultifeed.libmultifeed()


######################################################################################################################
## MAIN


programs = []


# -- relaunch down stream processes --
mtf.get_analyze_process(mtf.launcher)


# -- check for programs down and relaunch --
for i in programs:
	if mtf.get_process_program(i) == 0:
		mtf.run_program(i)


# -- wait 30 seconds and check for launcher and programs again --
mtf.get_fecha_hora()
seconds = 30 - mtf.fh['sec']

if mtf.debug_mode > 1:
	print("Sleeping "+str(seconds)+" seconds ...")

if seconds <= 30 and seconds >= 0:
	time.sleep(seconds)
	mtf.get_fecha_hora()
	mtf.get_analyze_process(mtf.launcher)

	# -- check for programs down and relaunch --
	for i in programs:
		if mtf.get_process_program(i) == 0:
			mtf.run_program(i)


