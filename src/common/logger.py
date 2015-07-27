import logging

def get_logger(name, filename, level=logging.INFO):
	logging.basicConfig(level=level, filename=filename)
	return logging.getLogger(name)
