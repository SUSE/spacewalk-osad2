import os
import zmq
from zmq.auth.ioloop import IOLoopAuthenticator
from zmq.eventloop import ioloop, zmqstream

from src.server.config import ServerConfig
from src.server.server import Server



def setup_auth_keys(config):
    """
    :param config: ServerConfig
    """
    public_keys_dir = os.path.join(config.get_certificates(), 'public_keys')
    private_keys_dir = os.path.join(config.get_certificates(), 'private_keys')

    if not (os.path.exists(public_keys_dir) and
            os.path.exists(private_keys_dir)):
        msg = ("Certificates are missing: %s and %s - "
               "run generate_certificates script first" %
               (public_keys_dir, private_keys_dir))
        config.get_logger(__name__).critical(msg)
        raise Exception(msg)

    auth = IOLoopAuthenticator()
    # auth.allow('127.0.0.1')

    # Tell authenticator to use the certificate in a directory
    auth.configure_curve(domain='*', location=public_keys_dir)

    secret_file = os.path.join(private_keys_dir, "server.key_secret")
    public_file = os.path.join(public_keys_dir, "server.key")

    return secret_file, public_file


def setup_stream(context, socket_type, secret_file, public_file):
    stream = context.socket(socket_type)

    server_public, server_secret = zmq.auth.load_certificate(secret_file)
    stream.curve_secretkey = server_secret
    stream.curve_publickey = server_public
    stream.curve_server = True

    return stream

PROD_CONFIG_PATH = '/etc/rhn/osad/osad_server.cfg'
TEST_CONFIG_PATH = 'etc/osad_server.test.cfg'


if __name__ == '__main__':
    loop = ioloop.IOLoop()
    context = zmq.Context()
    config = ServerConfig(TEST_CONFIG_PATH)

    secret_file, public_file = setup_auth_keys(config)

    router = setup_stream(context, zmq.ROUTER, secret_file, public_file)
    router.bind('tcp://%s:%d' % (config.get_bind(), config.get_listener_port()))
    instream = zmqstream.ZMQStream(router, loop)

    pub = setup_stream(context, zmq.PUB, secret_file, public_file)
    pub.bind('tcp://%s:%d' % (config.get_bind(), config.get_publisher_port()))
    outstream = zmqstream.ZMQStream(pub, loop)

    Server(loop, outstream, instream, config)

    loop.start()
