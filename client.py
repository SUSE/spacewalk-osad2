import os.path
import zmq
from zmq.auth.ioloop import IOLoopAuthenticator

from src.client.config import ClientConfig
from src.client.client import Client

DEFAULT_CONFIG_FILE = '/etc/sysconfig/rhn/osad.conf'
TEST_CONFIG_FILE = 'etc/osad_client.test.cfg'


def setup_stream(context, socket_type, client_secret_file, server_public_file):
    stream = context.socket(socket_type)
    client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
    stream.curve_secretkey = client_secret
    stream.curve_publickey = client_public

    server_public, _ = zmq.auth.load_certificate(server_public_file)
    stream.curve_serverkey = server_public
    return stream


if __name__ == '__main__':

    config = ClientConfig(TEST_CONFIG_FILE)
    logger = config.get_logger(__name__)

    if not os.path.exists(config.get_server_public_key_file()):
        logger.fatal('server public key missing: %s' % config.get_server_public_key_file())
        exit(1)
    if not os.path.exists(config.get_client_secret_key_file()):
        logger.fatal('client secret key missing: %s' % config.get_client_secret_key_file())
        exit(1)

    ctx = zmq.Context()
    listener = ctx.socket(zmq.SUB)

    auth = IOLoopAuthenticator()

    # Tell authenticator to use the certificate in a directory
    auth.configure_curve(domain='*', location=config.get_default_keys_dir())

    logger.info("Connecting to %s" % config.get_server_host())
    listener = setup_stream(ctx, zmq.SUB, config.get_client_secret_key_file(), config.get_server_public_key_file())
    listener.setsockopt(zmq.SUBSCRIBE, config.get_system_topic() % config.get_system_name())
    listener.setsockopt(zmq.SUBSCRIBE, config.get_ping_topic())
    listener.connect(config.get_server_producer())
    logger.info("Event stream connected to %s" % config.get_server_host())

    ponger = setup_stream(ctx, zmq.DEALER, config.get_client_secret_key_file(), config.get_server_public_key_file())
    ponger.setsockopt(zmq.IDENTITY, config.get_system_name())
    ponger.connect(config.get_server_consumer())
    logger.info("Heartbeat stream connected to %s" % config.get_server_host())

    client = Client(config, listener, ponger)

    client.start()