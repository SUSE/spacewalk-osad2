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
"""OSAD Server using libsodium encryption. The encryption keys and
certificate must be generated first, using generate_certificates.py

"""

import ConfigParser
import logging
import os.path
import time

import zmq
from zmq.auth.ioloop import IOLoopAuthenticator
from zmq.eventloop import ioloop, zmqstream

from src.server import smdb

CFG = ConfigParser.ConfigParser()
CFG.readfp(open('/etc/rhn/osad/osad_server.cfg'))

if CFG.getboolean('main', 'debug'):
    log_level = logging.DEBUG
else:
    log_level = logging.INFO
logging.basicConfig(level=log_level, filename=CFG.get('main', 'log_file'))
LOG = logging.getLogger(__name__)


class Server(object):
    """OSAD server class, uses two ZMQ streams to send and receive commands

    loop: Tornado IOLoop
    pingstream: a PUB stream
    pongstream: a ROUTER stream

    """
    _TOPICS = {'system': 'system:%s',
               'ping': 'ping'}

    def __init__(self, loop, pingstream, pongstream):
        self.pingstream = pingstream
        self.pongstream = pongstream
        self.pongstream.on_recv(self.handle_input)

        self.hearts = set()
        self.responses = set()
        self.lifetime = 0
        self.tic = time.time()

        self.checkin_count = CFG.getint('main', 'checkin_count')

        self.caller = ioloop.PeriodicCallback(
            self.beat, CFG.getint('main', 'ping_interval') * 1000, loop)
        self.action_poll_interval = CFG.getint('main', 'action_poll_interval')
        self.last_action_poll = time.time()

        self.smdb = smdb.SMDB()
        self.changed_state = []

        LOG.info("Starting OSAD server.")
        self.caller.start()

    def ping_check(self):
        """Updates and returns the time-based string we use to check ping age"""
        toc = time.time()
        self.lifetime += toc - self.tic
        self.tic = toc
        LOG.debug("%s" % self.lifetime)
        return str(self.lifetime)

    def ping_all(self):
        """Ping everyone following the ping_topic"""
        self.pingstream.send("%s %s" % (self._TOPICS['ping'],
                                        self.ping_check()))

    def handle_new_heart(self, heart):
        LOG.info("Yay, got a new heart %s!" % heart)
        self.hearts.add(heart)

    def handle_heart_failure(self, heart):
        LOG.warn("Heart %s failed :(" % heart)
        self.hearts.remove(heart)

    def recalculate_client_states(self):
        """Recalculate client states

        States could have changed asynchronously with messages received
        from clients.

        Returns a list of clients with changed states as dicts, e.g.:
        [{'id': 'client_name', 'state': 'offline'}]

        """
        online = self.hearts.intersection(self.responses)
        just_failed = self.hearts.difference(online)
        [self.handle_heart_failure(h) for h in just_failed]

        just_found = self.responses.difference(online)
        [self.handle_new_heart(h) for h in just_found]

        self.responses = set()

        LOG.debug("%i beating hearts: %s" % (len(self.hearts), self.hearts))

        self.changed_state.extend(
            [{'id': c, 'state': 'online'} for c in just_found]
            + [{'id': c, 'state': 'offline'} for c in just_failed])

    def beat(self):
        """This method is run once every PING_INTERVAL"""
        self.ping_all()

        self.recalculate_client_states()

        # TODO do this async
        self.update_client_states()
        self.checkin_clients(self.hearts)

        LOG.debug("---")

    def _its_time_to_checkin(self):
        return self.last_action_poll + self.action_poll_interval < time.time()

    def checkin_clients(self, hearts):
        """Go through all online clients and tell them to checkin"""
        if not self._its_time_to_checkin():
            return

        self.last_action_poll = time.time()
        nodes = self.smdb.get_checkin_clients(hearts, self.checkin_count)
        if nodes:
            LOG.info("Telling nodes to checkin: %s" % nodes)

            [self.pingstream.send("%s checkin" % self._TOPICS['system'] % system)
             for system in nodes]

    def update_client_states(self):
        """Update the client states in the database

        changed_state: a list of dicts representing clients which need
        to have their state updated in the database e.g.
        [{'id': 'client_name', 'state': 'offline'}]

        """
        if self.changed_state:
            LOG.debug("Updating states for:\n" +
                      "\n".join(["%s --> %s" % (c['id'], c['state'])
                                 for c in self.changed_state]))
            self.smdb.update_client_states(self.changed_state)
            self.changed_state = []

    def handle_input(self, msg):
        """if heart is beating"""
        topic, message = self.parse_message(msg)

        if topic == self._TOPICS['ping']:
            if message == str(self.lifetime):
                self.responses.add(msg[0])
            else:
                LOG.warn("got bad heartbeat (possibly old?): %s ..." % message)
        else:
            LOG.warn("Unknown message received: %s" % msg)

    def parse_message(self, msg):
        LOG.debug("Got: %s" % msg)
        identity, rest = msg
        topic, message = rest.split()
        return topic, message


def setup_auth_keys():
    certs_dir = CFG.get('main', 'certificates')
    public_keys_dir = os.path.join(certs_dir, 'public_keys')
    private_keys_dir = os.path.join(certs_dir, 'private_keys')

    if not (os.path.exists(public_keys_dir) and
            os.path.exists(private_keys_dir)):
        msg = ("Certificates are missing: %s and %s - "
               "run generate_certificates script first" %
               (public_keys_dir, private_keys_dir))
        LOG.critical(msg)
        raise Exception(msg)

    auth = IOLoopAuthenticator()
    # auth.allow('127.0.0.1')

    # Tell authenticator to use the certificate in a directory
    auth.configure_curve(domain='*', location=public_keys_dir)

    secret_file = os.path.join(private_keys_dir, "server.key_secret")
    public_file = os.path.join(public_keys_dir, "server.key")

    return secret_file, public_file


def setup_stream(context, socket_type, secret_file, public_file):
    stream = context.socket(socket_type)

    server_public, server_secret = zmq.auth.load_certificate(secret_file)
    stream.curve_secretkey = server_secret
    stream.curve_publickey = server_public
    stream.curve_server = True

    return stream


if __name__ == '__main__':
    loop = ioloop.IOLoop()
    context = zmq.Context()

    secret_file, public_file = setup_auth_keys()

    router = setup_stream(context, zmq.ROUTER, secret_file, public_file)
    router.bind('tcp://%s:%d' % (CFG.get('main', 'bind'),
                                 CFG.getint('main', 'listener_port')))
    instream = zmqstream.ZMQStream(router, loop)

    pub = setup_stream(context, zmq.PUB, secret_file, public_file)
    pub.bind('tcp://%s:%d' % (CFG.get('main', 'bind'),
                              CFG.getint('main', 'publisher_port')))
    outstream = zmqstream.ZMQStream(pub, loop)

    hb = Server(loop, outstream, instream)

    loop.start()
