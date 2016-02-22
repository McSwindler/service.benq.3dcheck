import time
import re
import xbmc, xbmcaddon, xbmcvfs
import simplejson as json
from BenQSocket import BenQSocket
 
__addon__ = xbmcaddon.Addon()

class TreeDMonitor(xbmc.Monitor):
	_currentMode = 'off'
	
	def __init__(self, *args, **kwargs):
		self.startupSocket()
	
	def onSettingsChanged(self):
		xbmc.log("Setting Changed", xbmc.LOGDEBUG)
		self.startupSocket()
	
	def onNotification(self, sender, method, data):
		if method == 'Player.OnPlay' or method == 'Player.OnStop':
			self.check3D()
			
		xbmc.log("Notification: %s %s %s" % (sender, method, json.loads(data)), xbmc.LOGDEBUG)
	
	def getDevice(self):
		dev = __addon__.getSetting('serial_device')
		m = re.search('^([^\s]+)', dev)
		if m is not None:
			if m.group(1) == 'TCP-IP':
				return 'socket://%s:%s' % (__addon__.getSetting('serial_ip'), __addon__.getSetting('serial_port'))
			else:
				return m.group(1)
		else:
			return ''
		
	def startupSocket(self):
		self.projector = BenQSocket(self.getDevice())
		self.check3D()
		
	def check3D(self):
		xbmc.log('Checking 3D mode.', xbmc.LOGDEBUG)
		query = '{"jsonrpc": "2.0", "method": "GUI.GetProperties", "params": {"properties": ["stereoscopicmode"]}, "id": 1}'
		result = xbmc.executeJSONRPC(query)
		data = json.loads(result)
		mode = 'unknown'
		if data.has_key('result'):
			if data['result'].has_key('stereoscopicmode'):
				if data['result']['stereoscopicmode'].has_key('mode'):
					mode = data['result']['stereoscopicmode']['mode'].encode('utf-8')
		xbmc.log('Received 3D mode: %s' % mode, xbmc.LOGDEBUG)
		
		if self._currentMode != mode:
			self.change3DMode(mode)
		
	def change3DMode(self, mode):
		self._currentMode = mode
		if mode == 'split_vertical':
			xbmc.log('Switching 3D to SBS', xbmc.LOGNOTICE)
			self.projector.set3DSBS()
		elif mode == 'split_horizontal':
			xbmc.log('Switching 3D to TAB', xbmc.LOGNOTICE)
			self.projector.set3DTAB()
		else:
			xbmc.log('Switching 3D to off', xbmc.LOGNOTICE)
			self.projector.set3DOff()
			
	def die(self):
		self.change3DMode('off')
		self.projector.kill()
		
def removeOldDevices(dir):
	dirs, files = xbmcvfs.listdir(dir)
	for f in files:
		xbmcvfs.delete(dir + f)
		
def populateDevices():
	import serial.tools.list_ports
	ports = [__addon__.getLocalizedString(33004)]
	ports += list(serial.tools.list_ports.comports())
	profile = __addon__.getAddonInfo('profile') + 'devices/'
	xbmcvfs.mkdirs(profile)
	removeOldDevices(profile)
	xbmc.log('Writing devices to %s' % profile, xbmc.LOGDEBUG)
	for port in ports:
		xbmc.log('Found Serial Device: %s' % port, xbmc.LOGNOTICE)
		f = xbmcvfs.File(profile + str(port) + '.rm', 'w')
		f.close()
		
if __name__ == '__main__':
	populateDevices()
	monitor = TreeDMonitor()
	while not monitor.abortRequested():
		if monitor.waitForAbort(1):
			break
		monitor.check3D()
	monitor.die() #Kodi is closing, turn off 3D