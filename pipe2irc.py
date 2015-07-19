#!/usr/bin/python
#
# Copyright (C) 2015 Oxan van Leeuwen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
      self.logger.info('Joined %d IRC channel(s)', len(self.args.channel))

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
      self.logger.info('Starting to send pipe to IRC')
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
parser.add_argument('--verbose', action='store_true', help='verbose output')
parser.add_argument('--debug', action='store_true', help='debug output')

args = parser.parse_args()
if(not os.path.exists(args.pipe)):
   sys.stderr.write("Pipe '%s' does not exist\n" % args.pipe)
   sys.exit(1)

# setup logging
syslog_handler = logging.handlers.SysLogHandler(address='/dev/log', facility=logging.handlers.SysLogHandler.LOG_DAEMON)
syslog_handler.setFormatter(logging.Formatter("pipe2irc: %(name)s: %(message)s"))
output_logger = logging.getLogger('' if args.debug else 'pipe2irc')
output_logger.setLevel(logging.DEBUG)
output_logger.addHandler(syslog_handler)
if (args.verbose):
   verbose_handler = logging.StreamHandler(stream=sys.stderr)
   verbose_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)-20s %(message)s"))
   output_logger.addHandler(verbose_handler)

# run the bot
PipeServingBot(args).start()
