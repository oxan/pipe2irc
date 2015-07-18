#!/usr/bin/python

import argparse
import logging
import logging.handlers
import os
import sys

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
logger = logging.getLogger('pipe2irc')