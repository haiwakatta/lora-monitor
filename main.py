import time
import binascii
import pycom
import socket
from machine import I2C
from struct import unpack
from network import LoRa

off = 0x000000
red = 0xff0000
green = 0x00ff00
blue = 0x0000ff

class Chirp:
	def __init__(self, address):
		self.i2c = I2C(0, I2C.MASTER, baudrate=10000)
		self.address = address

	def get_reg(self, reg):
		val = unpack('<H', (self.i2c.readfrom_mem(self.address, reg, 2)))[0]
		return (val >> 8) + ((val & 0xFF) << 8)

	def moist(self):
		return self.get_reg(0)

	def temp(self):
		return self.get_reg(5)

	def light(self):
		self.i2c.writeto(self.address, '\x03')
		time.sleep(1.5)
		return self.get_reg(4)

class LoRaNetwork:
	def __init__(self):
		# Turn off hearbeat LED
		pycom.heartbeat(False)
		# Initialize LoRaWAN radio
		self.lora = LoRa(mode=LoRa.LORAWAN)
		# Set network keys
		app_eui = binascii.unhexlify('70B3D57EF0003F19')
		app_key = binascii.unhexlify('4BA446ECCF1AB9398B0485561095297C')
		# Join the network
		self.lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
		pycom.rgbled(red)
		# Loop until joined
		while not self.lora.has_joined():
			print('Not joined yet...')
			pycom.rgbled(off)
			time.sleep(0.1)
			pycom.rgbled(red)
			time.sleep(2)
		print('Joined')
		pycom.rgbled(blue)
		self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
		self.s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
		self.s.setblocking(True)
		self.bytesarraytemp = bytearray(3)
		#sensor
		addr = 0x20 #or 32
		self.chirp = Chirp(addr)

	def convertbytes(self, data, sensor_id):
		self.bytesarraytemp[1] = (data & 0xFF00) >> 8
		self.bytesarraytemp[2] = (data & 0x00FF) 
		self.bytesarraytemp[0] = sensor_id
		return self.bytesarraytemp
	
	def senddata(self):
		while True:
			count = self.s.send(self.convertbytes(self.chirp.temp(), 0xAA))	
			print(count)
			count = self.s.send(self.convertbytes(self.chirp.moist(), 0xBB))	
			print(count)
			count = self.s.send(self.convertbytes(self.chirp.light(), 0xCC))
			print(count)
			pycom.rgbled(green)
			time.sleep(0.1)
			pycom.rgbled(blue)
			time.sleep(59.9)

start = LoRaNetwork()
start.senddata()
