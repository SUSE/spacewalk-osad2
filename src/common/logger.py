import logging

def get_logger(name, level=logging.INFO, filename):
	logging.basicConfig(level=level, filename=filename)
	return logging.getLogger(name)
