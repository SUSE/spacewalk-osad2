import zmq
from zmq.auth.ioloop import IOLoopAuthenticator
from zmq.eventloop import ioloop, zmqstream

from osad import smdb


def setup_auth_keys():
    certs_dir = CFG.get('main', 'certificates')
    public_keys_dir = os.path.join(certs_dir, 'public_keys')
    private_keys_dir = os.path.join(certs_dir, 'private_keys')

    if not (os.path.exists(public_keys_dir) and
            os.path.exists(private_keys_dir)):
        msg = ("Certificates are missing: %s and %s - "
               "run generate_certificates script first" %
               (public_keys_dir, private_keys_dir))
        LOG.critical(msg)
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

DEFAULT_CONFIG_PATH = '/etc/rhn/osad/osad_server.cfg'

if __name__ == '__main__':
    loop = ioloop.IOLoop()
    context = zmq.Context()

    secret_file, public_file = setup_auth_keys()

    router = setup_stream(context, zmq.ROUTER, secret_file, public_file)
    router.bind('tcp://%s:%d' % (CFG.get('main', 'bind'),
                                 CFG.getint('main', 'listener_port')))
    instream = zmqstream.ZMQStream(router, loop)

    pub = setup_stream(context, zmq.PUB, secret_file, public_file)
    pub.bind('tcp://%s:%d' % (CFG.get('main', 'bind'),
                              CFG.getint('main', 'publisher_port')))
    outstream = zmqstream.ZMQStream(pub, loop)

    config = ServerConfig(DEFAULT_CONFIG_PATH)

    hb = Server(loop, outstream, instream, config)

    loop.start()
