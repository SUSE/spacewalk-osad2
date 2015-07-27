import ConfigParser
import logging

class ServerConfig(ConfigParser.ConfigParser):
	
	def __init__(self, config_path):
		self.readfp(open(config_path))

	def get_logger(self, name):
		if self.getboolean('main', 'debug'):
		    log_level = logging.DEBUG
		else:
		    log_level = logging.INFO
		logging.basicConfig(level=log_level, filename=self.get('main', 'log_file'))
		return logging.getLogger(name)

	def get_checking_count(self):
        return self.getint('main', 'checkin_count')

    def get_ping_interval(self):
    	return config.getint('main', 'ping_interval')

    def get_action_poll_interval(self):
    	return config.getint('main', 'action_poll_interval')
