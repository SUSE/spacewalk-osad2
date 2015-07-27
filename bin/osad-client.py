#!/usr/bin/env python
#
# Copyright (c) 2014-2015 SUSE LLC
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

# pylint: disable-msg=C0103
"""OSAD Client using libsodium encryption. The encryption keys and
certificate must be generated first, using generate_certificates.py

"""
import sys
sys.path.append('/usr/share/rhn')
import ConfigParser
import os.path
import time
import logging
import subprocess
import argparse
from time import sleep

import zmq
from zmq.auth.ioloop import IOLoopAuthenticator
from zmq import devices

from rhn import rpclib
from up2date_client.config import initUp2dateConfig
from up2date_client import config

# interval to retry register with Spacewalk as push client
OSAD_REGISTER_RETRY_INTERVAL = 20
DEFAULT_CONFIG_FILE = '/etc/sysconfig/rhn/osad.conf'
DEFAULT_KEYS_DIR = '/etc/rhn/osad-client'

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='count', dest='debug',
                    help='enable debug logging')
parser.add_argument('-c', '--config',
                    default=DEFAULT_CONFIG_FILE,
                    dest='config_file',
                    help='alternative configuration file')
parser.add_argument('-k', '--keys-dir',
                    default=DEFAULT_KEYS_DIR,
                    dest='keys_dir',
                    help='alternative keys directory')
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)
if args.debug > 0:
    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SERVER_PUBLIC_KEY_FILE = os.path.join(args.keys_dir, "server.key")
CLIENT_SECRET_KEY_FILE = os.path.join(args.keys_dir, "client.key_secret")

if not os.path.exists(SERVER_PUBLIC_KEY_FILE):
    logger.fatal('server public key missing: %s' % SERVER_PUBLIC_KEY_FILE)
    exit(1)
if not os.path.exists(CLIENT_SECRET_KEY_FILE):
    logger.fatal('client secret key missing: %s' % CLIENT_SECRET_KEY_FILE)
    exit(1)

cfg = initUp2dateConfig()
SERVER_URL = cfg['serverURL']

config = ConfigParser.ConfigParser()
config.readfp(open(args.config_file))
systemid_path = config.get('osad', 'systemid')
with open(systemid_path) as f:
    systemid = f.read()

serverrpc = rpclib.Server(uri=SERVER_URL)

with open(systemid_path) as f:
    systemid = f.read()

ret = None
while ret is None:
    logger.info("registering as push client with %s..." % SERVER_URL)
    try:
        ret = serverrpc.registration.register_osad(systemid,
                                           {'client-timestamp': int(time.time())})
    except Exception as e:
        logger.error(e)
        logger.info("waiting %d seconds..." % OSAD_REGISTER_RETRY_INTERVAL)
        sleep(OSAD_REGISTER_RETRY_INTERVAL)

SERVER_HOST = ret['jabber-server']
SYSTEM_NAME = ret['client-name']
SERVER_PRODUCER = 'tcp://%s:5555' % SERVER_HOST
SERVER_CONSUMER = 'tcp://%s:5556' % SERVER_HOST
PING_TOPIC = "ping"
SYSTEM_TOPIC = "system:%s"
RHN_CHECK_COMMAND = config.get('osad', 'rhn_check_command')

ctx = zmq.Context()
listener = ctx.socket(zmq.SUB)

def setup_stream(context, socket_type, client_secret_file, server_public_file):
    stream = context.socket(socket_type)
    client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
    stream.curve_secretkey = client_secret
    stream.curve_publickey = client_public

    server_public, _ = zmq.auth.load_certificate(server_public_file)
    stream.curve_serverkey = server_public
    return stream

# Start an authenticator for this context.
auth = IOLoopAuthenticator()
# auth.allow('127.0.0.1')

# Tell authenticator to use the certificate in a directory
auth.configure_curve(domain='*', location=args.keys_dir)

logger.info("Connecting to %s" % SERVER_HOST)
listener = setup_stream(ctx, zmq.SUB, CLIENT_SECRET_KEY_FILE, SERVER_PUBLIC_KEY_FILE)
listener.setsockopt(zmq.SUBSCRIBE, SYSTEM_TOPIC % SYSTEM_NAME)
listener.setsockopt(zmq.SUBSCRIBE, PING_TOPIC)
listener.connect(SERVER_PRODUCER)
logger.info("Event stream connected to %s" % SERVER_HOST)

ponger = setup_stream(ctx, zmq.DEALER, CLIENT_SECRET_KEY_FILE, SERVER_PUBLIC_KEY_FILE)
ponger.setsockopt(zmq.IDENTITY, SYSTEM_NAME)
ponger.connect(SERVER_CONSUMER)
logger.info("Heartbeat stream connected to %s" % SERVER_HOST)

def do_ping(reply):
    # TODO don't block
    ponger.send(reply)
    logger.debug("pong -> %s" % SERVER_HOST)

def do_checkin():
    if do_checkin.process and do_checkin.process.poll() is None:
        logger.info("not checking in yet: rhn_check is already running...")
        return

    logger.info("checkin request from %s" % SERVER_HOST)
    try:
        cmd = [RHN_CHECK_COMMAND]
        if args.debug > 0:
            cmd.append('-vvv')
        # do not wait
        do_checkin.process = subprocess.Popen(cmd)
    except OSError as e:
        logger.error("Can't execute rhn_check: %s" % e.strerror)
    except Exception as e:
        logger.error("Can't execute rhn_check: %s" % e.message)

AVAILABLE_CMDS = {'checkin': do_checkin}

def handle_message(msg):
    logger.debug("Got '%s' from %s" % (msg, SERVER_HOST))
    topic, cmd = msg.split(None, 1)
    if topic == PING_TOPIC:
        do_ping(msg)
    elif topic == (SYSTEM_TOPIC % SYSTEM_NAME):
        try:
            AVAILABLE_CMDS[cmd]()
        except KeyError:
            logger.error("Unknown command '%s' from %s" % (cmd, SERVER_HOST))

do_checkin.process = None
while True:
    if do_checkin.process is not None:
        retcode = do_checkin.process.poll()
        if (retcode is not None):
            logger.info("rhn_check exited with status %d" % retcode)
            do_checkin.process = None
    tic = time.time()
    handle_message(listener.recv())
    logger.debug("waited %.3f s" % (time.time() - tic))
