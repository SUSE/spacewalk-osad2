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
import os, sys
import signal
import daemon
import lockfile
import argparse

from src.client.config import ClientConfig
from src.client.client import Client

DEFAULT_CONFIG_FILE = '/etc/sysconfig/rhn/osad.conf'
TEST_CONFIG_FILE = 'etc/osad_client.test.cfg'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        default=TEST_CONFIG_FILE,
                        dest='config_file',
                        help='alternative configuration file')
    parser.add_argument('--daemon',
                        dest='daemon',
                        action='store_true',
                        help='run as daemon')
    parser.add_argument('--no-daemon',
                        dest='daemon',
                        action='store_false',
                        help='run as shell process')
    parser.set_defaults(daemon=False)

    args = parser.parse_args()

    config = ClientConfig(args.config_file)
    client = Client(config)


    if args.daemon:
        print "terminatin %s " % os.path.isfile(config.get_pid_file())
        print config.get_pid_file()

        pidfile = lockfile.FileLock(config.get_pid_file())

        if pidfile.is_locked():
            sys.exit("FATAL: lock file %s already exists" % config.get_pid_file())

        def terminate(signum, frame):
            client.stop()

        context = daemon.DaemonContext(
            working_directory='/',
            umask=0o002,
            pidfile=pidfile,
            signal_map = {
                signal.SIGTERM: terminate,
                signal.SIGHUP: terminate
            },
            stderr = sys.stderr,
            stdout = sys.stdout
        )

        with context:
            client.start()
    else:
        client.start()


