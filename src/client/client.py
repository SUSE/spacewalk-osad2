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

import os.path
import zmq
from zmq.auth.ioloop import IOLoopAuthenticator
from src.client.handler import ClientHandler
from src.service import Service

class Client(Service):

    def start(self):
        ctx = zmq.Context()

        self.__authenticate()

        self.logger.info("Connecting to %s" % self.config.get_server_host())

        listener = ctx.socket(zmq.SUB)
        listener = self.__setup_stream(ctx, zmq.SUB, self.config.get_client_secret_key_file(), self.config.get_server_public_key_file())
        listener.setsockopt(zmq.SUBSCRIBE, self.config.get_system_topic() % self.config.get_system_name())
        listener.setsockopt(zmq.SUBSCRIBE, self.config.get_ping_topic())
        listener.connect(self.config.get_server_producer())
        self.logger.info("Event stream connected to %s" % self.config.get_server_host())

        ponger = self.__setup_stream(ctx, zmq.DEALER, self.config.get_client_secret_key_file(), self.config.get_server_public_key_file())
        ponger.setsockopt(zmq.IDENTITY, self.config.get_system_name())
        ponger.connect(self.config.get_server_consumer())
        self.logger.info("Heartbeat stream connected to %s" % self.config.get_server_host())

        self.add_on_close(lambda: ctx.close())

        client = ClientHandler(self.config, listener, ponger)
        client.start()

    def __authenticate(self):
        if not os.path.exists(self.config.get_server_public_key_file()):
            self.logger.fatal('server public key missing: %s' % self.config.get_server_public_key_file())
            exit(1)
        if not os.path.exists(self.config.get_client_secret_key_file()):
            self.fatal('client secret key missing: %s' % self.config.get_client_secret_key_file())
            exit(1)
        auth = IOLoopAuthenticator()

        # Tell authenticator to use the certificate in a directory
        auth.configure_curve(domain='*', location=self.config.get_default_keys_dir())

    def __setup_stream(self, context, socket_type, client_secret_file, server_public_file):
        stream = context.socket(socket_type)
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
        stream.curve_secretkey = client_secret
        stream.curve_publickey = client_public

        server_public, _ = zmq.auth.load_certificate(server_public_file)
        stream.curve_serverkey = server_public

        self.add_on_close(lambda: context.zmq_close(stream))

        return stream
