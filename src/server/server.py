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

import time

from zmq.eventloop import ioloop

from src.server import smdb


class Server(object):
  """OSAD server class, uses two ZMQ streams to send and receive commands

  loop: Tornado IOLoop
  pingstream: a PUB stream
  pongstream: a ROUTER stream

  """
  _TOPICS = {'system': 'system:%s',
             'ping': 'ping'}

  def __init__(self, loop, pingstream, pongstream, config):
    self.pingstream = pingstream
    self.pongstream = pongstream
    self.pongstream.on_recv(self.handle_input)

    self.hearts = set()
    self.responses = set()
    self.lifetime = 0
    self.tic = time.time()

    self.logger = config.get_logger(__name__)

    self.checkin_count = config.get_checkin_count()

    self.caller = ioloop.PeriodicCallback(self.beat, config.get_ping_interval() * 1000, loop)
    self.action_poll_interval = config.get_action_poll_interval()
    self.last_action_poll = time.time()

    self.smdb = smdb.SMDB()
    self.changed_state = []

    self.logger.info("Starting OSAD server.")
    self.caller.start()

  def ping_check(self):
    """Updates and returns the time-based string we use to check ping age"""
    toc = time.time()
    self.lifetime += toc - self.tic
    self.tic = toc
    self.logger.debug("%s" % self.lifetime)
    return str(self.lifetime)

  def ping_all(self):
    """Ping everyone following the ping_topic"""
    self.pingstream.send("%s %s" % (self._TOPICS['ping'],
                                    self.ping_check()))

  def handle_new_heart(self, heart):
    self.logger.info("Yay, got a new heart %s!" % heart)
    self.hearts.add(heart)

  def handle_heart_failure(self, heart):
    self.logger.warn("Heart %s failed :(" % heart)
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

    self.logger.debug("%i beating hearts: %s" % (len(self.hearts), self.hearts))

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

    self.logger.debug("---")

  def _its_time_to_checkin(self):
    return self.last_action_poll + self.action_poll_interval < time.time()

  def checkin_clients(self, hearts):
    """Go through all online clients and tell them to checkin"""
    if not self._its_time_to_checkin():
      return

    self.last_action_poll = time.time()
    nodes = self.smdb.get_checkin_clients(hearts, self.checkin_count)
    if nodes:
      self.logger.info("Telling nodes to checkin: %s" % nodes)

      [self.pingstream.send("%s checkin" % self._TOPICS['system'] % system)
       for system in nodes]

  def update_client_states(self):
    """Update the client states in the database

    changed_state: a list of dicts representing clients which need
    to have their state updated in the database e.g.
    [{'id': 'client_name', 'state': 'offline'}]

    """
    if self.changed_state:
      self.logger.debug("Updating states for:\n" +
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
        self.logger.warn("got bad heartbeat (possibly old?): %s ..." % message)
    else:
      self.logger.warn("Unknown message received: %s" % msg)

  def parse_message(self, msg):
    self.logger.debug("Got: %s" % msg)
    identity, rest = msg
    topic, message = rest.split()
    return topic, message
