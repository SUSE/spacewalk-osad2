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

from src.server.config import ServerConfig
from src.server.server import Server


PROD_CONFIG_PATH = '/etc/rhn/osad/osad_server.cfg'
TEST_CONFIG_PATH = 'etc/osad_server.test.cfg'

if __name__ == '__main__':
    config = ServerConfig(TEST_CONFIG_PATH)
    server = Server(config)
    server.start()
