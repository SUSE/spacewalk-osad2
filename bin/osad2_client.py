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
import argparse
import os
import sys


OSAD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RHN_ROOT = os.path.join(OSAD_ROOT, os.pardir)

for path in (OSAD_ROOT, RHN_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)



from osad2.client.config import ClientConfig
from osad2.client.client import Client
from osad2.daemonize import daemonize

DEFAULT_CONFIG_FILE = '/etc/sysconfig/rhn/osad.conf'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        default=DEFAULT_CONFIG_FILE,
                        dest='config_file',
                        help='alternative configuration file')
    parser.add_argument('-d', '--daemon',
                        dest='daemon',
                        action='store_true',
                        help='run as daemon',
                        default=False)
    args = parser.parse_args()

    config = ClientConfig(args.config_file)
    client = Client(config)

    if args.daemon:
        daemonize(client)
    else:
        try:
            client.start()
        finally:
            client.stop()
