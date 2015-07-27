import ConfigParser
import logging


class ServerConfig(object):
  def __init__(self, config_path):
    self.config = ConfigParser.ConfigParser()
    self.config.readfp(open(config_path))

  def get_logger(self, name):
    log_level = logging.DEBUG if self.config.getboolean('main', 'debug') else logging.INFO
    logging.basicConfig(level=log_level, filename=self.config.get('main', 'log_file'))
    return logging.getLogger(name)

  def get_checkin_count(self):
    return self.config.getint('main', 'checkin_count')

  def get_ping_interval(self):
    return self.config.getint('main', 'ping_interval')

  def get_action_poll_interval(self):
    return self.config.getint('main', 'action_poll_interval')

  def get_bind(self):
    return self.config.get('main', 'bind')

  def get_listener_port(self):
    return self.config.getint('main', 'listener_port')

  def get_publisher_port(self):
    return self.config.getint('main', 'publisher_port')

  def get_certificates(self):
    return self.config.get('main', 'certificates')
