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

import os
import zmq
from zmq.auth.ioloop import IOLoopAuthenticator
from zmq.eventloop import ioloop, zmqstream
from src.server.logic import ServerLogic


class Server(object):
    def __init__(self, config):
        self.config = config

    def start(self):
        loop = ioloop.IOLoop()
        context = zmq.Context()
        secret_file, public_file = self.__authenticate(self.config)

        router = self.__setup_stream(context, zmq.ROUTER, secret_file, public_file)
        router.bind('tcp://%s:%d' % (self.config.get_bind(), self.config.get_listener_port()))
        instream = zmqstream.ZMQStream(router, loop)

        pub = self.__setup_stream(context, zmq.PUB, secret_file, public_file)
        pub.bind('tcp://%s:%d' % (self.config.get_bind(), self.config.get_publisher_port()))
        outstream = zmqstream.ZMQStream(pub, loop)

        ServerLogic(loop, outstream, instream, self.config)

        loop.start()

    def __authenticate(self):
        public_keys_dir = self.config.get_public_keys_dir()
        private_keys_dir = self.config.get_private_keys_dir()

        if not (os.path.exists(public_keys_dir) and os.path.exists(private_keys_dir)):
            msg = ("Certificates are missing: %s and %s - "
                   "run generate_certificates script first" %
                   (public_keys_dir, private_keys_dir))
            self.config.get_logger(__name__).critical(msg)
            raise Exception(msg)

        auth = IOLoopAuthenticator()
        auth.configure_curve(domain='*', location=public_keys_dir)

        secret_file = os.path.join(private_keys_dir, "server.key_secret")
        public_file = os.path.join(public_keys_dir, "server.key")

        return secret_file, public_file

    def __setup_stream(self, context, socket_type, secret_file):
        stream = context.socket(socket_type)

        server_public, server_secret = zmq.auth.load_certificate(secret_file)
        stream.curve_secretkey = server_secret
        stream.curve_publickey = server_public
        stream.curve_server = True

        return stream
