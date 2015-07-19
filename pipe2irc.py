#!/usr/bin/python

from __future__ import division

import argparse
import irc.bot
import logging
import logging.handlers
import math
import os
import sys
import threading

VERSION = "0.1"
NAME = "pipe2irc"

class PipeServingBot(irc.bot.SingleServerIRCBot):
   def __init__(self, args):
      super(PipeServingBot, self).__init__([(args.server, args.port)], args.nick, args.nick, 1)
      self.logger = logging.getLogger('pipe2irc.bot')
      self.args = args

   def get_version(self):
      return "{0}/{1}".format(NAME, VERSION)

   def on_welcome(self, connection, event):
      for channel in self.args.channel:
         connection.join(channel)
      self.logger.debug('Joined IRC channels')

      self.log_thread = LogServingThread(self.args, self)
      self.log_thread.daemon = True
      self.log_thread.start()

class LogServingThread(threading.Thread):
   def __init__(self, args, bot):
      super(LogServingThread, self).__init__()
      self.logger = logging.getLogger('pipe2irc.logthread')
      self.args = args
      self.bot = bot

   def run(self):
      while True:
         self.logger.debug('Reopening input pipe')
         with open(args.pipe) as handle:
            while True:
               log_line = handle.readline()
               if not log_line:
                  break
               for i in range(0, int(math.ceil(len(log_line) / 300))):
                  msg  = "(continued) " if i != 0 else ""
                  msg += log_line[i*300:(i+1)*300].strip()
                  for channel in self.args.channel:
                     self.bot.connection.privmsg(channel, msg.strip())

# parse arguments
parser = argparse.ArgumentParser(description='Broadcast a named pipe to IRC')
parser.add_argument('--server', required=True, help='IRC server to join')
parser.add_argument('--port', default=6667, help='port of the IRC server')
parser.add_argument('--nick', required=True, help='nick to use on the IRC server')
parser.add_argument('--channel', action='append', required=True, help='channel to join')
parser.add_argument('--pipe', required=True, help='pipe to read from')

args = parser.parse_args()
if(not os.path.exists(args.pipe)):
	sys.stderr.write("Pipe '%s' does not exist\n" % args.pipe)

# setup logging to syslog
formatter = logging.Formatter("pipe2irc: %(name)s: %(message)s")
handler = logging.handlers.SysLogHandler(address='/dev/log', facility=logging.handlers.SysLogHandler.LOG_DAEMON)
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.DEBUG)

# run the bot
PipeServingBot(args).start()
