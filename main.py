from network import Bluetooth
import binascii
from machine import I2C
import time
from struct import unpack

def uuid2bytes(uuid):
    uuid = uuid.encode().replace(b'-',b'')
    tmp = binascii.unhexlify(uuid)
    return bytes(reversed(tmp))

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

bluetooth = Bluetooth()
bluetooth.set_advertisement(name='LoPy', service_uuid=b'1234567890123456')

def conn_cb (bt_o):
    events = bt_o.events()
    if  events & Bluetooth.CLIENT_CONNECTED:
        print("Client connected")
    elif events & Bluetooth.CLIENT_DISCONNECTED:
        print("Client disconnected")

bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=conn_cb)

bluetooth.advertise(True)

addr = 0x20 #or 32
chirp = Chirp(addr)

srv2 = bluetooth.service(uuid=uuid2bytes('00001110-2222-1002-8010-00805F9B34FB'), isprimary=True)

chr2 = srv2.characteristic(uuid=uuid2bytes('82460002-4098-1000-8666-00805F9B34FB'), value=chirp.moist())
char2_read_counter = chirp.moist()
def char2_cb_handler(chr):
    global char2_read_counter
    char2_read_counter = chirp.moist()
    return char2_read_counter

char2_cb = chr2.callback(trigger=Bluetooth.CHAR_READ_EVENT, handler=char2_cb_handler)
