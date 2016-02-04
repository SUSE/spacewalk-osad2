#!/usr/bin/env python

from distutils.core import setup, run_setup, Command
import zmq.auth
import os

OSAD2_PATH = os.path.dirname(os.path.realpath(__file__))
OSAD2_SERVER_CERTS_DIR = "/etc/rhn/osad2-server/certs/"
OSAD2_CLIENT_SETUP_FILE = os.path.join(OSAD2_PATH, "setup_client.py")
PKGNAME_FILE = os.path.join(OSAD2_PATH, "PKGNAME")


class OSAD2Command(Command):
    def _create_curve_certs(self, name):
        print "Creating CURVE certificates for '%s'..." % name
        pk_file, sk_file = zmq.auth.create_certificates(OSAD2_SERVER_CERTS_DIR,
                                                        name)

        print pk_file
        print sk_file
        # FIXME: copy to tmp dir for RPM creation


class CreateServerCommand(OSAD2Command):
    description = "Create and install CURVE server key"
    user_options = []

    def initialize_options(self):
        self.name = None

    def finalize_options(self):
        assert os.path.isdir(OSAD2_SERVER_CERTS_DIR), \
          'Certificates storage dir doesn\'t exist: %s' % OSAD2_SERVER_CERTS_DIR

        server_keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, 'server.key')
        assert not os.path.isfile(server_keyfile), 'Server key already exists'

    def run(self):
        self._create_curve_certs("server")
        exit(0)


class CreateClientCommand(OSAD2Command):
    description = "Create a new client. Generate a RPM package"
    user_options = [
        ('name=', None, 'Specify the new client name.'),
    ]

    def initialize_options(self):
        self.name = None

    def finalize_options(self):
        assert self.name, 'You must specify a client name'
        assert os.path.isdir(OSAD2_SERVER_CERTS_DIR), \
          'Certificates storage dir doesn\'t exist: %s' % OSAD2_SERVER_CERTS_DIR

        keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, self.name + '.key')
        server_keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, 'server.key')

        assert os.path.isfile(server_keyfile), 'Server key doesn\'t exist'
        assert not os.path.isfile(keyfile), 'Client name already exists'

    def run(self):
        self._create_curve_certs(self.name)
        self._build_client_rpm()
        exit(0)

    def _build_client_rpm(self):
        print "Creating RPM package for '%s'..." % self.name
        open(PKGNAME_FILE, "w").write(self.name)
        run_setup(OSAD2_CLIENT_SETUP_FILE, script_args=["bdist_rpm", "--quiet"])
        os.remove(PKGNAME_FILE)


setup(name='spacewalk-osad2-server',
      version='alpha',
      license='GPLv2',
      description='An alternative OSA dispatcher module for Spacewalk',
      long_description='This is an experiment to improve osad, a service '
                       'that simulates instant execution of actions in a '
                       'Spacewalk environment.',

      platforms=['All'],

      packages=['osad2', 'osad2.server'],
      scripts=['bin/osad2_server.py'],

      data_files=[
                  ('/etc/rhn/osad2-server/', ['etc/osad_server.prod.cfg']),
                  ('/etc/rhn/osad2-server/certs/', []),
                ],

      cmdclass={'createclient': CreateClientCommand,
                'createserver': CreateServerCommand})
