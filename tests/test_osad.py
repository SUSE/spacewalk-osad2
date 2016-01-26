""" Tests for `the_project` module. """

import pytest
import os
import src


ROOTDIR = os.path.dirname(src.__path__[0])
OSAD_ROOT = '/usr/share/rhn/osad'


@pytest.fixture()
def spacewalk(docker, container):
    return container(
        'horneds/spacewalk_osad',
        volumes=OSAD_ROOT, name='spacewalk_test',
        host_config=docker.create_host_config(binds=["%s:%s" % (ROOTDIR, OSAD_ROOT)])
    )


def test_client_cli(spacewalk, docker):
    CMD = "/usr/bin/python %s/bin/client.py --help" % OSAD_ROOT
    proc = docker.exec_create(spacewalk, CMD)
    output = docker.exec_start(proc)
    assert 'show this help message and exit' in output

    info = docker.exec_inspect(proc)
    assert not info['ExitCode']


#  def test_client_starts(spacewalk, docker):
    #  CMD = "/usr/bin/python {0}/bin/client.py -c {0}/tests/client.cfg -d".format(OSAD_ROOT)
    #  proc = docker.exec_create(spacewalk, CMD)
    #  output = docker.exec_start(proc)


def test_server_cli(spacewalk, docker):
    CMD = "/usr/bin/python %s/bin/server.py --help" % OSAD_ROOT
    proc = docker.exec_create(spacewalk, CMD)
    output = docker.exec_start(proc)
    assert 'show this help message and exit' in output

    info = docker.exec_inspect(proc)
    assert not info['ExitCode']


def test_server_starts(spacewalk, docker):
    CMD = "/usr/bin/python {0}/bin/server.py -c {0}/tests/server.cfg -d".format(OSAD_ROOT)
    proc = docker.exec_create(spacewalk, CMD)
    docker.exec_start(proc)
    info = docker.exec_inspect(proc)
    assert not info['ExitCode']

    proc = docker.exec_create(spacewalk, 'test -r /var/log/osad-server')
    docker.exec_start(proc)
    info = docker.exec_inspect(proc)
    assert not info['ExitCode']
