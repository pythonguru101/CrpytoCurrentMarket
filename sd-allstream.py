#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import commands
#import subprocess
import libmultifeed

mtf = libmultifeed.libmultifeed()


######################################################################################################################
## MAIN


# -- define variables --
mtf.path = os.getcwd()+"/"
mtf.launcher = mtf.path+"allstream.py"
mtf.histo_launcher = mtf.path+"allhistorical.py"
mtf.process_file = mtf.path+"multifeed-process.txt"
mtf.process_histo_file = mtf.path+"multifeed-histo-process.txt"


# -- kill processes --
#mtf.kill_all_process()
#mtf.kill_all_histo_process()

# -- kill process by pid --
comando = "ps auwx | egrep 'allstream\.py|allhistorical\.py' | grep -v 'grep' | awk {'print $2'}"
#result = commands.getoutput(comando).split("\n")
result = subprocess.getoutput(comando).split("\n")
for i in result:
	print i
	mtf.kill_process_by_pid(i)


