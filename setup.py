#!/usr/bin/env python

from distutils.core import setup, run_setup, Command
import zmq.auth
import os

OSAD2_SERVER_CERTS_DIR="/etc/rhn/osad2/certs/"
OSAD2_CLIENT_SETUP_FILE="setup_client.py"
PKGNAME_FILE="PKGNAME"


class CreateClientCommand(Command):
    description = "Create a new client. Generate a RPM package"
    user_options = [
        ('name=', None, 'Specify the new client name.'),
    ]

    def initialize_options(self):
        self.name = None

    def finalize_options(self):
        assert self.name, 'You must specify a client name'

	keyfile = os.path.join(OSAD2_SERVER_CERTS_DIR, self.name + ".key")
	assert not os.path.isfile(keyfile), 'Client name already exists'
             
    def run(self):
        print "Creating CURVE certificates for '%s'..." % self.name
        pk_file, sk_file = zmq.auth.create_certificates(OSAD2_SERVER_CERTS_DIR,
                                                        self.name)

        print pk_file
        print sk_file

        print "Creating RPM package for '%s'..." % self.name
        self.__build_client_rpm()
        exit(0)

    def __build_client_rpm(self):
	open(PKGNAME_FILE,"w").write(self.name)
        _build = run_setup(OSAD2_CLIENT_SETUP_FILE,
                           script_args=["bdist_rpm", "--quiet"])
	os.remove(PKGNAME_FILE)
    

setup(name='spacewalk-osad2-server',
      version='alpha',
      license='GPLv2',
      description='An alternative OSA dispatcher module for Spacewalk',
      long_description='This is an experiment to improve osad, a service '
                       'that simulates instant execution of actions in a '
                       'Spacewalk environment.',

      platforms=['All'],

      packages=['src', 'bin'],

      data_files=[
                  ('/etc/rhn/osad2/', ['etc/osad_server.prod.cfg']),
                  ('', ['setup.py', 'setup.cfg']),
                ],

      cmdclass={
           'createclient': CreateClientCommand,
      }
     )
