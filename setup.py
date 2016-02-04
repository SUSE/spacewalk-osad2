#!/usr/bin/env python

from distutils.core import setup, run_setup, Command
import zmq.auth
import shutil
import os

OSAD2_PATH = os.path.dirname(os.path.realpath(__file__))

OSAD2_SERVER_CERTS_DIR = "/etc/rhn/osad2-server/certs/"
OSAD2_SERVER_PUB_KEY = os.path.join(OSAD2_SERVER_CERTS_DIR, "public_keys/server.key")
OSAD2_SERVER_PRIVATE_KEY = os.path.join(OSAD2_SERVER_CERTS_DIR, "private_keys/server.key_secret")

OSAD2_CLIENT_SETUP_FILE = os.path.join(OSAD2_PATH, "setup_client.py")
PKGNAME_FILE = os.path.join(OSAD2_PATH, "PKGNAME")


class OSAD2Command(Command):
    def _create_curve_certs(self, name):
        print "Creating CURVE certificates for '%s'..." % name
        pk_file, sk_file = zmq.auth.create_certificates(OSAD2_SERVER_CERTS_DIR,
                                                        name)

        # OSAD2 certificates storage
        pk_dst = os.path.join(OSAD2_SERVER_CERTS_DIR, "public_keys")
        sk_dst = os.path.join(OSAD2_SERVER_CERTS_DIR, "private_keys")

        shutil.move(pk_file, pk_dst)
        shutil.move(sk_file, sk_dst)

        pk_dst = os.path.join(pk_dst, name + ".key")
        sk_dst = os.path.join(sk_dst, name + ".key_secret")

        print pk_dst
        print sk_dst

        return pk_dst, sk_dst


class CreateServerCommand(OSAD2Command):
    description = "Create and install CURVE server key"
    user_options = []

    def initialize_options(self):
        self.name = None

    def finalize_options(self):
        assert os.path.isdir(OSAD2_SERVER_CERTS_DIR), \
          'Certificates storage dir doesn\'t exist: %s' % OSAD2_SERVER_CERTS_DIR

        server_keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, 'private_keys/server.key_secret')
        assert not os.path.isfile(server_keyfile), 'Server key already exists'

    def run(self):
        self._create_curve_certs("server")


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

        keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, "public_keys/" + self.name + '.key')
        server_keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, 'private_keys/server.key_secret')

        assert os.path.isfile(server_keyfile), 'Server key doesn\'t exist'
        assert not os.path.isfile(keyfile), 'Client name already exists'

    def run(self):
        pk_file, sk_file = self._create_curve_certs(self.name)

        # Temporary key storage for RPM build
        import shutil
        shutil.copy(pk_file, "etc/client.key_secret")
        shutil.copy(OSAD2_SERVER_PUB_KEY, "etc/")
        self._build_client_rpm()

    def _build_client_rpm(self):
        print "Creating RPM package for '%s'..." % self.name
        open(PKGNAME_FILE, "w").write(self.name)
        run_setup(OSAD2_CLIENT_SETUP_FILE, script_args=["bdist_rpm", "--quiet"])
        os.remove(PKGNAME_FILE)
        os.remove("etc/client.key_secret")
        os.remove("etc/server.key")


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
                  ('/etc/rhn/osad2-server/certs/private_keys/', []),
                  ('/etc/rhn/osad2-server/certs/public_keys/', []),
                ],

      cmdclass={'createclient': CreateClientCommand,
                'createserver': CreateServerCommand})
