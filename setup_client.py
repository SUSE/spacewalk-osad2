#!/usr/bin/env python

from distutils.core import setup
import os

PKGNAME = 'spacewalk-osad2-client'

if os.path.isfile("PKGNAME"):
   PKGNAME += "-" + open("PKGNAME","r").readline()

setup(name=PKGNAME,
      version='alpha',
      license='GPLv2',
      description='An alternative OSA dispatcher module for Spacewalk',
      long_description='This is an experiment to improve osad, a service that '
                       'simulates instant execution of actions in a Spacewalk '
                       'environment.',

      platforms=['All'],

      packages=['src', 'bin'],

      data_files=[
                  ('/etc/rhn/osad2/', ['etc/osad_client.prod.cfg']),
                ])
