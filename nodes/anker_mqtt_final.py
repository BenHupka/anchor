import paho.mqtt.client as mqtt
import json
from ahoi.modem.modem import Modem
from ahoi.modem.packet import printPacket, isCmdType
import time
from network_management.address_book import ADDRESS_BOOK
from network_management.utils import load_ahoi_config, get_host_ip, get_hostname

USE_FAKE_MODEM = False
TARGET_AHOI_ID = 9
# TARGET_AHOI_ID = 255

# workaround to get the buoy id from host ip
# host_ip = get_host_ip()
# use the last digit of the ip to get the buoy id
# buoy_id = int(host_ip.split(".")[-1])
# buoy_id = 5 #TODO: replace with automatically retrieving buoy 1 via ip or hostname
# buoy_topic = "buoy_" + str(buoy_id)

#use hostname
hostname = get_hostname()
# split at "-" to get the buoy id
buoy_id = int(hostname.split("-")[-1])
buoy_topic = "buoy_" + str(buoy_id)

# MQTT configuration
broker_address = ADDRESS_BOOK["mqtt_broker"].eth_ip
port = 1883

topics = [
    buoy_topic + "/global_info", buoy_topic + "/local_info",
    buoy_topic + "/status"
]

id = TARGET_AHOI_ID

if USE_FAKE_MODEM:
    port_modem = "FakeConnection"
    THIS_MODEM_ID = 203
else:
    config = load_ahoi_config()
    # Modem Configuration
    THIS_MODEM_ID = config["modem_id"]
    port_modem = config["modem_port"]
    # port_modem = "/dev/ttyUSB0" # NOTE: override if necessary

position_north = -123
position_east = -123


# Called when connection to the broker is established
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to broker: " + broker_address)

    # Subscribe to all topics once connected
    for topic in topics:
        client.subscribe(topic)

    print("Subscribed to topics: " + str(topics))


# Called when a message is received, update position
def on_message(client, userdata, msg):
    global position_north, position_east
    # Decode the message's payload and convert from JSON
    payload = json.loads(msg.payload.decode())

    if msg.topic == buoy_topic + "/local_info":
        position_north = payload["north"]
        position_east = payload["east"]
        print(f"Received new position: {position_north}, {position_east}")


# Modem Callback
def anchorCallback(pkt):
    if not isCmdType(pkt):
        print("Received Ahoi Packet:")
        printPacket(pkt)

    # check if initial position is requested (Pakettyp 0x7C = 124)
    if pkt.header.type == 0x7C and pkt.header.dst == THIS_MODEM_ID:
        position_n = position_north
        position_e = position_east
        position = position_n.to_bytes(
            2, 'big', signed=True) + position_e.to_bytes(2, 'big', signed=True)
        myModem.send(
            dst=TARGET_AHOI_ID,
            payload=position,
            status=
            0,  #NOTE: it's not necessary to provide src argument (will be ignored)
            type=0x7B)  # initiale Ankerposition übertragen (Pakettyp 0x7B)
        print(f"\n[ANCHOR] Sent initial position: {position_n}, {position_e}\n")

    # check if position is requested (Pakettyp 0x7E = 126)
    if pkt.header.type == 0x7E and pkt.header.dst == THIS_MODEM_ID:
        time.sleep(
            1)  # wait before sending position, ranging ACK is sent before
        position_n = position_north
        position_e = position_east
        position = position_n.to_bytes(
            2, 'big', signed=True) + position_e.to_bytes(2, 'big', signed=True)
        myModem.send(dst=TARGET_AHOI_ID, payload=position, status=0,
                     type=0x7D)  # Ankerposition übertragen (Pakettyp 0x7D)
        print(f"\n[ANCHOR] Sent position: {position_n}, {position_e}\n")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, port=port)

myModem = Modem()
myModem.connect(port_modem)
print("Connected to ahoi modem on port: " + port_modem)

myModem.addRxCallback(anchorCallback)
myModem.receive(thread=True)

try:
    # Blocking loop to keep the client running
    client.loop_forever()
except KeyboardInterrupt:
    print("Disconnecting from broker and modem.")
    client.disconnect()
    myModem.close()
