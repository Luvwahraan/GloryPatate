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

from classes import Handler, Privileges, Channel

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


#        Privileges( notext=False, firstmsg=False, returning=False,
#               follower=False, subscriber=False, turbo=False,
#               vip=False, moderator=False, owner=False)


hd.addCommand('join',
        lambda v: hd.joinChannel( Channel(v.message[1], 0) ),
        'Join channel', 
        Privileges( notext=False, firstmsg=False, returning=False,
               follower=False, subscriber=False, turbo=False,
               vip=False, moderator=True, owner=True))

while True:
    try:
        hd.messageloop()
    except KeyboardInterrupt:
        print("\nBot killed\n\n")
        exit()
        raise
    except:
        if hd.except_count > 4:
            print('Too many errors.')

        hd.except_count += 1
        
        print(traceback.format_exc())
        hd.socketconnection()
        hd.messageloop()
        