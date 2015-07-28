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

import time
import subprocess


class ClientHandler(object):
    def __init__(self, config, listener, ponger):
        self.config = config
        self.listener = listener
        self.ponger = ponger
        self.logger = config.get_logger(__name__)

    def start(self):
        self.do_checkin_process = None
        while True:
            if self.do_checkin_process is not None:
                retcode = self.do_checkin_process.poll()
                if retcode is not None:
                    self.logger.info("rhn_check exited with status %d" % retcode)
                    self.do_checkin_process = None
            tic = time.time()
            self.handle_message(self.listener.recv())
            self.logger.debug("waited %.3f s" % (time.time() - tic))

    def handle_message(self, msg):

        available_cmds = {'checkin': self.do_checkin}

        self.logger.debug("Got '%s' from %s" % (msg, self.config.get_server_host()))
        topic, cmd = msg.split(None, 1)
        if topic == self.config.get_ping_topic():
            self.do_ping(msg)
        elif topic == (self.config.get_system_topic() % self.config.get_system_name()):
            try:
                available_cmds[cmd](self)
            except KeyError:
                self.logger.error("Unknown command '%s' from %s" % (cmd, self.config.get_server_host()))

    def do_ping(self, reply):
        self.ponger.send(reply)
        self.logger.debug("pong -> %s" % self.config.get_server_host())

    def do_checkin(self):
        if self.do_checkin_process and self.do_checkin_process.poll() is None:
            self.logger.info("not checking in yet: rhn_check is already running...")
            return

        self.logger.info("checkin request from %s" % self.config.get_server_host())
        try:
            cmd = [self.config.get_rhn_check_command()]
            if self.config.is_debug():
                cmd.append('-vvv')
            # do not wait
            self.do_checkin_process = subprocess.Popen(cmd)
        except OSError as e:
            self.logger.error("Can't execute rhn_check: %s" % e.strerror)
        except Exception as e:
            self.logger.error("Can't execute rhn_check: %s" % e.message)
