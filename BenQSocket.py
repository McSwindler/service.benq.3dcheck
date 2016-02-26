import serial
import time
import re
import xbmc,xbmcaddon
from xbmc import log
from xbmc import LOGERROR
from xbmc import LOGDEBUG
	
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')

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
			self.notify()
			log(str(e), LOGERROR)

	def _send(self, payload):
		if self.sock is None:
			return ''
			
		send = self.sock.write(payload)
		if send == 0:
			self.notify()
		self.sock.flush()
		time.sleep(1)
		return self._receive()
		
	def _receive(self):
		timeout = time.time() + 10
		buff = ''
		while True:
			try:
				r = self.sock.read(1)
			except serial.serialutil.SerialException as e:
				self.notify()
				log(str(e), LOGERROR)
			buff += r
			if buff.endswith('#\r\n'):
				break
			if r == '' and time.time() > timeout:
				self.notify()
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
			
	def notify(self, msg='Cannot connect to projector'):
		xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__, msg, 2000, __icon__))
		log(msg, LOGERROR)
		