import os

import docker as libdocker
import pytest


@pytest.fixture(scope='session')
def docker():
    """Initialize docker client."""
    certs = os.environ.get('DOCKER_CERT_PATH')
    host = os.environ.get('DOCKER_HOST')
    tls = None

    if certs:
        tls = libdocker.tls.TLSConfig(
            (os.path.join(certs, 'cert.pem'), os.path.join(certs, 'key.pem')),
            os.path.join(certs, 'ca.pem'), os.environ.get('DOCKER_TLS_VERIFY')
        )
        if host.startswith('tcp://'):
            host = host.replace('tcp://', 'https://')

    client = libdocker.Client(base_url=host, tls=tls)
    client.verify = False
    return client


@pytest.yield_fixture()
def container(docker):
    store = {'ID': None}

    def start(image, **params):
        store['ID'] = ID = docker.create_container(image, **params)['Id']
        docker.start(ID)
        return ID

    yield start

    if store['ID']:
        docker.kill(store['ID'])
        docker.remove_container(store['ID'])
