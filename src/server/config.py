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

import ConfigParser
import logging
import os


class ServerConfig(object):
    def __init__(self, config_path):
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(config_path))

    def get_logger(self, name):
        log_level = logging.DEBUG if self.is_debug() else logging.INFO
        logging.basicConfig(level=log_level, filename=self.config.get('main', 'log_file'))
        return logging.getLogger(name)

    def is_debug(self):
        return self.config.getboolean('main', 'debug')

    def get_checkin_count(self):
        return self.config.getint('main', 'checkin_count')

    def get_ping_interval(self):
        return self.config.getint('main', 'ping_interval')

    def get_action_poll_interval(self):
        return self.config.getint('main', 'action_poll_interval')

    def get_bind(self):
        return self.config.get('main', 'bind')

    def get_listener_port(self):
        return self.config.getint('main', 'listener_port')

    def get_publisher_port(self):
        return self.config.getint('main', 'publisher_port')

    def get_public_keys_dir(self):
        return os.path.join(self.config.get('main', 'certificates'), 'public_keys')

    def get_private_keys_dir(self):
        return os.path.join(self.config.get('main', 'certificates'), 'private_keys')

    def get_pid_file(self):
        return self.config.get('main', 'pidfile')
