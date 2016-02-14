import signal
import sys

import daemon
import lockfile


def daemonize(service):
    """Daemonize the given service."""
    pidfile = lockfile.FileLock(service.config.get_pid_file())

    if pidfile.is_locked():
        sys.exit("FATAL: lock file %s already exists" % service.config.get_pid_file())

    def terminate(signum, frame):
        service.stop()

    context = daemon.DaemonContext(
        working_directory='/',
        umask=0o002,
        pidfile=pidfile,
        signal_map={
            signal.SIGTERM: terminate,
            signal.SIGHUP: terminate
        }
    )

    with context:
        service.start()
