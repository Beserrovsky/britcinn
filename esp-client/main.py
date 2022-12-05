from components import *

# CONSTRAINTS

MQTT_HOSTNAME = 'broker.emqx.io'
MQTT_PORT = 1883

mqtt_server = socket.getaddrinfo(MQTT_HOSTNAME, MQTT_PORT)[0][4][0]

topic_prefix = 'britcinn'

last_will_topic = 'client'

dht_topic = 'dht'
light_topic = 'light'
light_state_topic = 'light_state'
servo_topic = 'servo'
servo_angle_topic = 'servo_angle'
switch_state_topic = 'switch'

RELAY_PIN = 19
SWITCH_PIN = 21
SERVO_PIN = 22
DHT11_PIN = 23


#########

client_id = ubinascii.hexlify(machine.unique_id())
cli_id = str(client_id.decode('utf8', 'strict'))

def connect(client_id, mqtt_server):
  print(f'{cli_id} connecting to {mqtt_server}')
  client = MQTTClient(client_id, mqtt_server)

  # Doesn't work at alll, emqx problem?
  client.set_last_will( f'{topic_prefix}/{last_will_topic}' , str(ujson.dumps( 
    {
      'client_id': cli_id,
      'status': False
    }
  )))
  client.set_callback(sub_cb)

  client.connect()

  print('Connected to MQTT broker')
  return client

def restart_and_reconnect():
  error_animation("Failed to connect to MQTT broker. Reconnecting...")
  time.sleep(10)
  machine.reset()

def subscribe():
  client.subscribe( f'{topic_prefix}/{light_topic}' )
  client.subscribe( f'{topic_prefix}/{servo_topic}' )

# Subscriptions

def sub_cb(topic, msg):
  topic = str(topic.decode('utf8', 'strict'))
  msg = str(msg.decode('utf8', 'strict'))
  print(f't: "{topic}" -> m:"{msg}"')

  if (topic == f'{topic_prefix}/{light_topic}'):
    changeLight(msg)

  if (topic == f'{topic_prefix}/{servo_topic}'):
    changeServo(msg)


def changeLight(msg):
  msg = ujson.loads(msg)
  components.relay.setRelayState(msg['light'], True)
  pass

def changeServo(msg):
  msg = ujson.loads(msg)
  components.servo.setServoAngle(msg['angle'], True)
  pass

# ! IMPORTANT CALLS !

client = None

## Connects to broker and subscribes to topics
def start():
  global client
  try:
    client = connect(client_id, mqtt_server)
    subscribe()
    client.publish( f'{topic_prefix}/{last_will_topic}' , str(ujson.dumps(
    {
      'client_id': cli_id,
      'status': True
    }
    )))
  except OSError as e:
    print(e)
    restart_and_reconnect()

## Checks incoming msgs
def tick():
  try:
    new_message = client.check_msg()
    if new_message != None: # Handled by sub_cb
      print(f'Message received!')
  except OSError as e:
    restart_and_reconnect()

## Updates sensors data
def updateMQTT(verbose = False):

  relayData = {
    'client_id': cli_id,
    'light_state': components.relay.getRelayState(verbose)
  }
  client.publish(f'{topic_prefix}/{light_state_topic}', str(ujson.dumps(relayData)))


  switchData = {
    'client_id': cli_id,
    'switch_state': components.switch.getSwitchState(verbose)
  }
  client.publish(f'{topic_prefix}/{switch_state_topic}', str(ujson.dumps(switchData)))


  servoData = {
    'client_id': cli_id,
    'servo_angle': components.servo.getServoAngle(verbose)
  }
  client.publish(f'{topic_prefix}/{servo_angle_topic}', str(ujson.dumps(servoData)))

  
  temp, hum = components.dht11.getDHT(verbose)
  dhtData = {
    'client_id': cli_id,
    'temp': temp,
    'hum': hum
  }
  client.publish(f'{topic_prefix}/{dht_topic}', str(ujson.dumps(dhtData)))

  
  print('\nData sent to broker!\n')

components = Components(RELAY_PIN, SWITCH_PIN, SERVO_PIN, DHT11_PIN)

MQTT_FREQUENCY = 5 # seconds between updates

def main():
  while True:
    last_time = time.time()
    tick()
    while ((time.time() - last_time) < MQTT_FREQUENCY):
      components.routine(True)
    updateMQTT(True)
    

start()
main()
