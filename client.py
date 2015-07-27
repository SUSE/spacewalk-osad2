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

from src.client.config import ClientConfig
from src.client.client import Client

DEFAULT_CONFIG_FILE = '/etc/sysconfig/rhn/osad.conf'
TEST_CONFIG_FILE = 'etc/osad_client.test.cfg'

if __name__ == '__main__':
    config = ClientConfig(TEST_CONFIG_FILE)
    client = Client(config)
    client.start()
