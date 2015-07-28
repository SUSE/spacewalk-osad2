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

import abc


class Service(object):
    def __init__(self, config):
        self.config = config
        self.logger = config.get_logger(self.__class__.__name__)
        self.on_close = []

    @abc.abstractmethod
    def start(self):
        pass

    def stop(self):
        for callback in self.on_close:
            callback()

    def add_on_close(self, callback):
        self.on_close.append(callback)
