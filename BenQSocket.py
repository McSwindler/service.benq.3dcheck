import serial
import time
import re
try:
	import xbmc
	from xbmc import log
	from xbmc import LOGERROR
	from xbmc import LOGDEBUG
except:
	import logging
	from logging import ERROR as LOGERROR
	from logging import DEBUG as LOGDEBUG

	logging.basicConfig(level=LOGDEBUG)

	def log(data, level):
		logging.log(level, data)

class BenQSocket:
	sock = None
	_format = "\r*3d=%s#\r"
	_regex = re.compile('(\w+)#')

	def __init__(self, device, baudrate=115200):
		try:
			self.sock = serial.serial_for_url(device)
			self.sock.baudrate = baudrate
			self.sock.timeout = 0
		except serial.serialutil.SerialException as e:
			log('Cannot connect to serial port', LOGERROR)
			log(str(e), LOGERROR)

	def _send(self, payload):
		if self.sock is None:
			return ''
			
		send = self.sock.write(payload)
		if send == 0:
			log('Cannot connect to projector', LOGERROR)
		self.sock.flush()
		time.sleep(1)
		return self._receive()
		
	def _receive(self):
		timeout = time.time() + 10
		buff = ''
		while True:
			r = self.sock.read(1)
			buff += r
			if buff.endswith('#\r\n'):
				break
			if r == '' and time.time() > timeout:
				log('Cannot connect to projector', LOGERROR)
				break
		m = self._regex.findall(buff)
		if not m:
			return buff
		else:
			return m[-1]

	def get3DMode(self):
		return self._send(self._format % '?')

	def set3DSBS(self):
		return self._send(self._format % 'sbs')

	def set3DTAB(self):
		return self._send(self._format % 'tb')

	def set3DOff(self):
		return self._send(self._format % 'off')

	def kill(self):
		try:
			if self.sock is not None:
				self.sock.close()
		finally:
			log('BenQSocket killed', LOGDEBUG)
