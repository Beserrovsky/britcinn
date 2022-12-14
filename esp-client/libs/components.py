import dht, time

from machine import *

class Relay:

  relay = None
  relay_state = False

  def __init__(self, relay_pin):
    self.relay = Pin(relay_pin, Pin.OUT)
  
  def setRelayState(self, state = None, verbose = False):
    if (state == None):
      self.relay_state = not self.relay_state
    else:
      self.relay_state = state
    
    self.relay.value(self.relay_state)
    if (verbose):
      print(f"Relay state: {self.relay_state}")

    return self.relay_state
  
  def getRelayState(self, verbose = False):
    if (verbose):
      print(f"Relay state: {self.relay_state}")

    return self.relay_state

class Switch:

  switch = None
  switch_state = False

  def __init__(self, switch_pin):
    self.switch = Pin(switch_pin, Pin.IN, Pin.PULL_DOWN)
    self.switch_state = (self.switch.value() == 1)
  
  def getSwitchChange(self, verbose = False):
    state = (self.switch.value() == 1)
    if (self.switch_state != state):
      self.switch_state = state
      if (verbose):
        print("Switch toggled!")
      return True
    else:
      return False
  
  def getSwitchState(self, verbose = False):
    if (verbose):
      print(f"Switch state: {self.switch_state}")

    return self.switch_state

class Servo:

  servo = None
  servo_angle = 0

  def __init__(self, servo_pin):
    self.servo = PWM(Pin(servo_pin))
    self.servo.freq(50)
    self.servo.duty(40)
  
  def setServoAngle(self, angle, verbose = False):
    self.servo_angle = angle

    duty = int(self.translate(self.servo_angle, 0, 180, 40, 115))
    self.servo.duty(duty)
    if (verbose):
      print(f"Servo angle altered to: {self.servo_angle}")
      print(f"Angle in duty cicle: {duty}")
    
    return self.servo_angle
  
  def getServoAngle(self, verbose = False):
    if (verbose):
      print(f"Servo angle: {self.servo_angle}")
    
    return self.servo_angle

  def translate(self, value, leftMin, leftMax, rightMin, rightMax): # Adam Luchjenbroers's function
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

class DHT11:
  
  dht11 = None
  temp = 0
  hum = 0

  def __init__(self, dht11_pin):
    self.dht11 = dht.DHT11(Pin(dht11_pin))
    self.getDHT()

  def getDHT(self, verbose = False):
    self.dht11.measure()
    self.temp = self.dht11.temperature()
    self.hum = self.dht11.humidity()
    if (verbose):
      print(f"Temperature: {self.temp}")
      print(f"Humidity: {self.hum}")

    return self.temp, self.hum

class Components:
  
  relay = None
  switch = None
  servo = None
  dht11 = None
  
  def __init__(self, relay_pin, switch_pin, servo_pin, dht11_pin):
    self.relay = Relay(relay_pin)
    self.switch = Switch(switch_pin)
    self.servo = Servo(servo_pin)
    self.dht11 = DHT11(dht11_pin)

    self.servo.setServoAngle(0)

  def routine(self, verbose = False):
    if (self.switch.getSwitchChange(verbose)):
      self.relay.setRelayState(None, verbose)
