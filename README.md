
# (the new) osad

*EXPERIMENTAL*

This is an experiment to improve Spacewalk component osad.

It was hacked during an internal SUSE workshop by

* [Ionuț Arțăriși](https://github.com/mapleoin)
* [Duncan Mac-Vicar P.](https://github.com/dmacvicar)

## About osad

osad is a service to simulate instant execution of actions in a Spacewalk environment.

## Design

The original osad was based on a jabber (XMPP) hub, with individual systems connected as clients (osad) and one agent (osad-dispatcher) running on the Spacewalk server polling actions from the database and then sending messages to the systems, notifying them to run rhn_check and pick up the actions from the server.

The original osad suffered from hard to debug issues due to jabberd corrupting its
database and connectivity issues between clients and the server.

The new osad is based on zmq (http://zeromq.org). It consists on two components:

* osad-server : creates a PUB socket and polls actions from the database that
  are published.
* osad-client : creates a SUB socket and executes rhn_check when an event
  is published

### Handshake

Handshake reuses some pieces from the old osad:

* Client register itself as a push client using the same XML-RPC call which
  associates the random client name with the server-side system.
  This uses osad_register_push_client to get a server host and a client-name.
  The client name is used as a topic for the PUB queue so that clients only
  get the relevant notifications.
* Client connects to the zmq sockets on osad-server and start getting events
  This connection uses a server public key to authenticate the server.
  zmq uses libsodium for this.

### TODO/issues/ideas

* Think how to test it, may be using Docker
* zmq with certificate deployment means deploying yet another certificate

