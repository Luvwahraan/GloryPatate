#!/usr/bin/python3

import socket
import string
import random
import time
import json
import os
import traceback
import re
import requests
import sys
import sqlite3
import math
import datetime
import re

from classes import Handler

try:
    PASS = sys.argv[1]
except:
    PASS = ''
try:
    DEBUG = sys.argv[2]
except:
    DEBUG = ''


print('Connecting server: ' + PASS)
hd = Handler('GloryPatate', PASS, True)


while True:
    try:
        hd.messageloop()
    except KeyboardInterrupt:
        print("\nBot killed\n\n")
        exit()
        raise
    except:
        if self.except_count > 4:
            print('Too many errors.')

        self.except_count += 1
        
        print(traceback.format_exc())
        hd.socketconnection()
        hd.messageloop()
        