from components import *

# CONSTRAINTS

mqtt_server = '3.124.50.83' # HiveMQ Broker

pub_prefix = 'britcinn'

#########

client_id = ubinascii.hexlify(machine.unique_id())

def connect(client_id, mqtt_server):
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()

  print('Connected to MQTT broker')
  return client

# def subscribe():
#   global sub_topic
#   client.subscribe(sub_topic)  

def restart_and_reconnect():
  error_animation("Failed to connect to MQTT broker. Reconnecting...")
  time.sleep(10)
  machine.reset()

# Subscriptions

def sub_cb(topic, msg):
  print(f't: "{topic}" -> m:"{msg}"')


# ! IMPORTANT CALLS !

client = None

## Connects to broker and subscribes to topics
def start():
  global client
  try:
    client = connect(client_id, mqtt_server)
    # subscribe(client)
  except OSError as e:
    print(e)
    restart_and_reconnect()

## Checks incoming msgs
def tick():
  try:
    new_message = client.check_msg()
    if new_message != None: # Handled by sub_cb
      print(f'Message received: {new_message}')
  except OSError as e:
    restart_and_reconnect()

## Updates sensors data
def update(ldr, temp, hum):
  cli_id = str(client_id.decode('utf8', 'strict')

  ldrD = {
    'client_id': cli_id),
    'ldr': ldr
  }

  dhtD = {
    'client_id': cli_id,
    'temp': temp,
    'hum': hum
  }

  client.publish(ldr_pub, str(ujson.dumps(ldrD)))
  client.publish(dht_pub, str(ujson.dumps(dhtD)))

  print('Data sent to broker!')


def main():
  components = C
  while True:


start()
main()
