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


class Privileges:
    def __init__(self, notext=False, returning=False, firstmsg=False, follower=False,
                subscriber=False, turbo=False, vip=False, moderator=False, owner=False):
        # Ordered highest to lower
        self.owner = owner
        self.moderator = moderator
        self.vip = vip
        self.subgifter = False
        self.turbo = turbo
        self.subscriber = subscriber
        self.partner = False
        self.partner = False
        self.follower = follower
        self.premium = False
        self.returning = returning
        self.firstmsg = firstmsg
        self.notext = notext
    
    def __eq__(self, pr):
        pself = self.__dict__
        ppr = pr.__dict__
        for attribut, value in pself.items():
            if ppr[attribut] != value:
                return False
        return True
    
    def __ge__(self, pr):
        if self > pr or self == pr:
            return True
        return False
    
    def __le__(self, pr):
        if self < pr or self == pr:
            return True
        return False
    
    def __ne__(self, pr):
        pself = self.__dict__
        ppr = pr.__dict__
        for attribut, value in pself.items():
            if ppr[attribut] != value:
                return True
        return False
    
    def __lt__(self, pr):
        pself = self.__dict__
        ppr = pr.__dict__
        for attribut, value in pself.items():
            if ppr[attribut] < value:
                return True
            elif value < ppr[attribut]:
                return False
        return False
    
    def __gt__(self, pr):
        pself = self.__dict__
        ppr = pr.__dict__
        for attribut, value in pself.items():
            if ppr[attribut] > value:
                return True
            elif value > ppr[attribut]:
                return False
        return False

class Viewer:
    def __init__(self, message):
        
        self.nick = ''
        self.channel = ''
        self.message = message
        self.words = []
        self.owner = False
        self.userid = 0
        self.channelid = 0
        self.ignored = False
        
        self.command = ''
        
        self.privileges = Privileges()
        
        self.addedChannel = []
        
        self.points = 10
        self.ratio = 10

        self.vip = False
        self.turbo = False
        self.moderator = False
        self.subscriber = False
        self.follower = False
        self.firstmsg = False
        self.notext = False
        self.returning = False
        self.badges = { 'broadcaster': 0, 'premium': 0, 'moderator': 0, 'partner': 0,
            'founder': -1, 'subscriber': 0, 'vip': 0, 'sub-gifter': 0}
        self.emotes = []
        
        self.mark = ''
    
    def __str__(self):
        return viewer.channel + ' <' + viewer.mark + viewer.nick + ' ' + str(viewer.points) + 'pts> ' + viewer.message
        return f"{self.nick})"

    def check_privileges(self):
        try:
            if self.badges['broadcaster'] > 0:
                self.mark = '&'
                self.privileges.owner = True
                self.points = 0
                return self.mark
            if self.badges['moderator'] > 0:
                self.mark += '@'
                self.privileges.moderator = True
            if self.badges['subscriber'] > 0:
                self.mark += '$('+ str(self.badges['subscriber']) +')'
                self.privileges.subscriber = True
                self.points += 9 + self.badges['subscriber']
                self.ratio += 5
            if self.badges['premium'] > 0:
                self.mark += '-'
                self.privileges.premium = True
                self.ratio -= 8
            if self.badges['sub-gifter'] > 0:
                self.mark += 'G('+ str(self.badges['sub-gifter']) +')'
                self.points += math.floor( self.badges['sub-gifter'] / 20 )
                self.privileges.subgifter = True
                self.ratio += 4
            if self.badges['partner'] > 0:
                self.mark += '̰~'
                self.privileges.partner = True
                self.ratio += 1
            if self.badges['vip'] > 0:
                self.mark += '̰*'
                self.points += 5
                self.privileges.vip = True
                self.ratio += 2
            if self.follower:
                self.mark += '+'
                self.privileges.follower = True
                self.points += 4
                self.ratio += 1
            if self.badges['founder'] >= 0:
                self.mark += '#'
                self.privileges.founder = True
                self.points += 2
                self.ratio += 3
            if self.firstmsg:
                self.mark += '(New)'
                self.privileges.firstmsg = True
                self.points += 100
            if self.returning:
                self.mark += '(New)'
                self.privileges.returning = True
                self.points += 100
        except:
            print(traceback.format_exc())

        return self.mark


class Command:
    def __init__(self, command, callback, description, privileges):
        self.name = command
        self.callback = callback
        self.description = description
        self.privileges = privileges

     
        
    def __str__(self):
        description = ''
        if self.description != '':
            description = ': ' + self.description
            
        return self.name + description


class Handler:
    def __init__(self, nick, oauth, debug=False):
        self.debug = debug
        self.except_count = 0

        self.commands = []

        self.nick = nick
        self.oauth = oauth
        self.port = 6667
        self.host = 'irc.twitch.tv'
        self.channels = []
        
        if self.debug:
            print('Debug active')
        else:
            print('No debug')
        
        self.dbfile = "{}".format(self.nick)+'.sqlite'
        self.readbuffer = ''
        
        self.s = socket.socket()
        self.initdb()
        self.connectIRC()
        
        
    def searchCommand(self, cmdName):
        for cmd in self.commands:
            if cmdName == cmd.name:
                return cmd
        return False



    def addCommand(self, name, callback, description, pr=Privileges( notext=False, firstmsg=False, returning=False,
               follower=False, subscriber=False, turbo=False,
               vip=False, moderator=False, owner=True)):
        if not self.searchCommand(name):            
            self.commands.append( Command(name, callback, description, pr) )
            return True
        return False

        
    def check_ignored(self, viewer):
        req = 'SELECT userid FROM ignored WHERE userid = ? AND channelid = ?'
        try:
            for response in self.cursor.execute(req, (viewer.userid, viewer.channelid)):
                return True
        except self.dbcon.Error:
            print('Failed searching user from ignored table')
        except:
            print(traceback.format_exc())

        return False
        
    def joinChannel(self, channel):
        self.ircSend('JOIN ' + channel.name)
        channel.connected = True
    
    
    def ircSend(self, data, forcedebug=False):
        self.s.send(bytes(data + "\r\n", "UTF-8"))
        if self.debug or forcedebug:
            print('>>> ' + data)

    def connectIRC(self):
        try:
            self.s.connect((self.host, self.port))
            #self.s.send(bytes("PASS %s\r\n" % self.oauth, "UTF-8"))
            self.ircSend('PASS ' + self.oauth )
            self.ircSend('NICK ' + self.nick )
            for chan in self.channels:
                self.joinChannel(chan)
            self.ircSend('CAP REQ :twitch.tv/membership')
            #self.ircSend('CAP REQ :twitch.tv/commands')
            self.ircSend('CAP REQ :twitch.tv/tags')
        except:
            print(traceback.format_exc())
            print('IRC failed')


    def socketconnection(self):
        try:
            self.s.socket.close()
            self.s.socket.socket.socket()
            self.connectIRC()
        except:
            print(traceback.format_exc())
            print('Connexion failed')
            exit()


    def addChannel(self, viewer):
        if len( viewer.words ) < 2:
            print('No channel given.')
            return False
        
        self.joinChannel( viewer.words[1] )
        viewer.addChannel.append( viewer.words[1] )
        
        if viewer.channelid <= 0:
            return False

        try:
            req = 'INSERT OR IGNORE INTO channels (channelid, channel) VALUES(?,?)'
            self.cursor.execute( req, (viewer.channelid, viewer.channel) )
            self.dbcon.commit()
            print('Added ' + viewer.channel + '(' + str(viewer.channelid) + ') to channels')
            return True
        except self.dbcon.Error:
            print('Failed adding ' + viewer.channel + '(' + str(viewer.channelid) + ') to channels')
        except:
            print(traceback.format_exc())

        return False

    def searchChannel(self, channel):
        pass
    
    def initdb(self):
        try:
            #opens channel database or creates new database if one does not already exist
            self.dbcon = sqlite3.connect(self.dbfile)
            self.cursor = self.dbcon.cursor()
            if not os.path.exists(self.dbfile):
                self.cursor.execute('CREATE TABLE users(userid INTEGER PRIMARY KEY, nick TEXT NOT NULL)')
                self.cursor.execute('CREATE TABLE userpoints(userid INTEGER PRIMARY KEY, channelid INTEGER NOT NULL, points INT DEFAULT 0)')
                self.cursor.execute('CREATE TABLE ignored(userid INTEGER PRIMARY KEY, channelid INTEGER NOT NULL)')
                self.cursor.execute('CREATE TABLE channels(channelid INTEGER PRIMARY KEY, channel TEXT NOT NULL UNIQUE)')
                self.dbcon.commit()
        except self.dbcon.Error:
            print('Failed creating tables')
        except:
            print(traceback.format_exc())
        
        # Searching channels to join
        self.getchannels()
    
    def getchannels(self):
        try:
            print('get channels')
            for x in  self.cursor.execute('SELECT channelid, channel FROM channels'):
                #self.joinChannel( x[1] )
                self.channels.append( Channel(x[1], x[0] ) )
                print( str(x[0]) + ' - ' + x[1] )
        except self.dbcon.Error:
            print('Cant searching channels')

    def givepoints(self, viewer):
        # Don’t give points to ignored user.
        if self.check_ignored(viewer): # or viewer.userid == viewers.channelid :
            return

        try:
            req = 'UPDATE userpoints '
            req += 'SET points = points + ? '
            req += 'WHERE userid = ? AND channelid = ? '                                        # update viewer’s points for specific channel
            req += 'AND EXISTS( SELECT 1 FROM channels WHERE channelid = ? ) '                  # but only in known channel
            req += 'AND NOT EXISTS( SELECT 1 FROM ignored WHERE userid = ? AND channelid = ?)'  # and only if user is not ignored
            
            self.cursor.execute( req, (viewer.points, viewer.channelid, viewer.userid, viewer.channelid, viewer.userid, viewer.channelid) )
            self.dbcon.commit()
            print('Giving ' + str(viewer.points) + ' points to ' + viewer.nick)
        except self.dbcon.Error:
            print('Failed giving points')
        except:
            print(traceback.format_exc())

    def sendmessage(self, channel, text):
        #####self.s.send(bytes("PRIVMSG " + str(channel) + " :" + str(text) + "\r\n", "UTF-8"))
        pass



    def messageloop(self):
        while True:
            try:
                self.readbuffer = self.readbuffer + self.s.recv(1024).decode("UTF-8") 
            except KeyboardInterrupt:
                raise
            except:
               print(traceback.format_exc())
            
            temp = str.split(self.readbuffer, "\r\n")
            #temp = [ str(e.encode('UTF-8')).rstrip() for e in temp ]
            self.readbuffer = temp.pop()
            
                   
            for line in temp:
                if self.debug:
                    print( '<<< ' + line )
                
                parts = str.split(line, ' ')
                
                match parts[0]:
                    case 'PING':
                        self.ircSend('PONG ' + parts[1][1:])
                        return

                match parts[2]:
                    case 'PRIVMSG':
                        if len(parts) > 4:
                            pass
                            parts[4] = parts[4][1:]
                            self.parsemsg(parts[0], parts[1], parts[2], parts[3], parts[4:] )

                #ircinfo = str.split(line, 'PRIVMSG')
                #if len(ircinfo) > 1:
                #    self.parsemsg(ircinfo)
                #else:
                #    pass
                    #print(line)



    def commandsHandler(self, viewer):
        try:
            wordCount = abs( len( viewer.message ) - 1 )
            
            
            if viewer.message[0][0] == '!':
                viewer.command = viewer.message[0][1:].lower()
                
                if self.debug:
                    print( viewer.nick + '(' + str(viewer.userid) +') tries command !' + viewer.command)
                
                cmd = self.searchCommand(viewer.command)
                try:
                    if cmd.privileges <= viewer.privileges:
                        print('Running cmd')
                        cmd.callback(viewer)
                    else:
                        print('No enough privileges.')
                except:
                    pass
                    print(traceback.format_exc())
                
            else:
                viewer.command = ''

            
            
            

                

            
            if viewer.notext: #or givePoints(viewer.userid):
                viewer.points = 0
                #print('no points')
            else:
                viewer.points += math.floor( viewer.ratio * wordCount / 10 )

            if viewer.points != 0:
                points = ' ' + str(viewer.points)+ 'pts> '
            else:
                points = ''
            print(viewer.channel + ' <' + viewer.mark + viewer.nick + points + '> '+ ' '.join(viewer.message) )

            # Autorize subs, followers, vip, and donators
            if viewer.subscriber:
                if viewer.message == "!love":
                    viewer.points -= 50
                    #sendmessage("ogeruLove jiosHearth elbepolyLove lordgr14Love mikl66frLovea narweePoney thecre83Love elbepolyMerci ")
            elif viewer.follower:
                pass
            elif viewer.vip:
                pass
            elif viewer.badges['sub-gifter'] >= 10:
                pass
            
            match viewer.message:
                case '!channels':
                    pass
                case '!patate':
                    pass
        except:
            print(traceback.format_exc())
            
        return viewer



    def parsemsg(self, tags, user, msgtype, channel, message):
        user = user[1:]
        viewer = Viewer(message)
        viewer.channel = channel.lower()
        tags = str.split( tags, ";")
        
        try:
            for userstate in tags:
                state = str.split(userstate, '=')
                match state[0]:
                    case 'emote-only':
                        if int(state[1]) == 1:
                            viewer.privileges.notext = True
                        #print(state[0])
                    case 'emotes':
                        viewer.emotes = str.split(state[1], '/')
                        #print(state[0])
                    case 'vip':
                        if int(state[1]) == 1:
                            viewer.privileges.vip = True
                        #print(state[0])
                    case 'display-name':
                        viewer.nick = state[1]
                    case 'room-id':
                        viewer.channelid = int( state[1] )
                        #print(state[0])
                    case 'user-id':
                        viewer.userid = int( state[1] )
                        #print(state[0])
                    case 'turbo':
                        if int(state[1]) == 1:
                            viewer.privileges.turbo = True
                        #print(state[0])
                    case 'subscriber':
                        if int(state[1]) == 1:
                            viewer.privileges.subscriber = True
                        #print(state[0])
                    case 'follower':
                        if int(state[1]) == 1:
                            viewer.privileges.follower = True
                        #print(state[0])
                    case 'first-msg':
                        if int(state[1]) == 1:
                            viewer.privileges.firstmsg = True
                        #print(state[0])
                    case 'returning-chatter':
                        if int(state[1]) == 1:
                            viewer.privileges.returning = True
                        #print(state[0])
                    case 'badges':
                        for badge in str.split( state[1], ',' ):
                            tmp = str.split( badge, '/' )
                            viewer.badges[tmp[0]] = int(tmp[1])
                        #print(state[0])
            
            viewer.check_privileges()

            #cursor.execute('CREATE TABLE users(userid INT PRIMARY KEY, nick TEXT NOT NULL)'
            #cursor.execute('CREATE TABLE userpoints(userid INT NOT NULL, channelid INTEGER NOT NULL, points INT DEFAULT 0)')
            #cursor.execute('CREATE TABLE ignored(userid INT NOT NULL, channelid INTEGER NOT NULL)')
            #cursor.execute('CREATE TABLE channels(channelid INTEGER PRIMARY KEY, channel TEXT NOT NULL UNIQUE)')
            try:
                self.cursor.execute('INSERT OR IGNORE INTO users (userid, nick) VALUES (?,?)', (viewer.userid, viewer.nick) )
                self.cursor.execute('INSERT OR IGNORE INTO userpoints (userid, channelid, points) VALUES (?,?,?)',(viewer.userid, viewer.channelid, '0'))
                if viewer.message != '' and viewer.userid != 0 and viewer.channelid != 0 and viewer.nick != '':
                    viewer = self.commandsHandler(viewer)
                    if viewer.points != 0:
                        #cursor.execute('INSERT OR IGNORE INTO viewers (userid, nick, channel, points) VALUES (?,?,?,?)',(viewer.userid, viewer.nick, viewer.channel, '0'))
                        self.givepoints( viewer )
                self.dbcon.commit()
            except self.dbcon.Error:
                print('Failed adding viewer')
            except:
                print(traceback.format_exc())
        except:
            pass



class Channel:
    def __init__(self, name, channelid):
        self.name = name
        self.channelid = channelid
        self.connected = False
    
    def __str__(self):
        return self.name + '(' + self.channelid + ')'