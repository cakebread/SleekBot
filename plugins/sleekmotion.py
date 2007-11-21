"""
    sleekmotion.py - An approximate port of bMotion to Sleek.
    Copyright (C) 2007 Kevin Smith

    SleekBot is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import logging
import re
import random

class sleekmotionstore(object):
    def __init__(self):
        self.chatiness = 1
        self.store = {}

    def loaddefault(self):
        self.load("sleekmotion.dat")

    def savedefault(self):
        self.save("sleekmotion.dat")

    def load(self, filename):
        try:
            f = open(filename, 'rb')
        except:
            logging.warning("Error loading sleekmotion config")
            return
        self = pickle.load(f)
        f.close()

    def save(self, filename):
        try:
            f = open(filename, 'wb')
        except IOError:
            logging.warning("Error saving sleekmotion config")
            return
        pickle.dump(self, f)
        f.close()
    

class sleekmotion(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.store = sleekmotionstore()
        self.store.loaddefault()
        self.about = "'sleekmotion' is an approximate port of bMotion to SleekBot.\nWritten By: Kevin Smith"
        #self.bot.addIMCommand('chatiness', self.handle_chatiness)
        #self.bot.addMUCCommand('chatiness', self.handle_chatiness)
        #self.bot.addHelp('chatiness', 'Chatiness command', "Multiplier for the chatiness of a bot.", 'chatiness 0-100')
        self.commands = []
        
    def registerTrigger(self, name, regexp, frequency, response):
        """ Add a trigger, with id 'name', triggered when text matches 'regexp', 
            with a frequency%, and where the response is either a list or function.
        """
        responses = None
        function = None
        if type(response) == type(self.registerTrigger):
            function = response
        else:
            responses = response
        command = {'regexp':trigger, 'frequency':frequency, 'function':function, 'responses':responses}
        self.commands[name] = command
    
    def store(self, varName, values):
        """ Adds the list of values to the variable in the store.
        """
        if value in values:
            if self.store.store[varName] == None:
                self.store.store[varName] = []
            if value not in self.store.store[varName]:
                self.store.store[varName].append(value)
        
    def ruser(self):
        """ Returns a random nickname that the bot knows about.
        """
        self.store['names'] = ["Kev",'albert','remko','textshell','hal','infiniti','psidekick','xepbot']
        return self.store['names'](random.randint(0,len(self.store[names])-1))
    
    def variableValue(self, varname):
        """ Return a random value from a variable.
        """
        return self.store[varname](random.randint(0,len(self.store[varname])-1))
        
    def parseResponse(self, response, message):
        """ Parses special strings out of the response.
        """
        r = re.compile('%ruser')
        
        modified = response
        
        while r.search(modified):
            user = self.ruser()
            modified = re.sub(r, user, modified)
            
        r = re.compile('%VAR\\{(?P<varname>.+)\\}')
        while not r.search(modified) == None:
            varname = r.search(modified).group('varname')
            modified = re.sub(r, self.variableValue(varname), modified)
        return modified
    
        
    def handle_message(self, message):
        body = msg.get('message', '')
        for trigger in self.commands.values():
            if re.compile(trigger.regexp).search(body):
                if not trigger.function == None:
                    response = self.commands[trigger](body, message)
                else:
                    response = trigger.responses(random.randint(0,len(trigger.responses)-1))
                
                response = self.parseResponse(response, message)
                
                if msg['type'] == 'groupchat':
                    self.sendMessage("%s" % message.get('room', ''), response, mtype=message.get('type', 'groupchat'))
                else:
                    self.sendMessage("%s/%s" % (message.get('jid', ''), message.get('resource', '')), response, mtype=message.get('type', 'chat'))
        
    