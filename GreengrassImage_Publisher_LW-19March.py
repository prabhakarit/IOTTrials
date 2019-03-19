# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
#
# This sample is used in the AWS IoT Greengrass Developer Guide: 
# https://docs.aws.amazon.com/greengrass/latest/developerguide/module3-I.html
#

## Issue pending - image quality not good ! Need to be checked.

#import greengrasssdk
import platform
from threading import Timer
import time
import math
import random
import pyrealsense2 as rs
import realsensesavecolorimage
import base64
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException
import logging
import argparse
import json
import os
import re

## core connection and certs
core_ip = "172.16.17.137"
core_port = "8883"
root_cert = "root-ca-cert.pem"
private_key = "04c805e1ed.private.key"
certificate = "04c805e1ed.cert.pem"
##

thingName = "Prabhakar_laptop"
AllowedActions = ['both', 'publish', 'subscribe']
topic_publish_file = "topic-publish.txt"
image_name="color_image_simple.png"
packet_size=3000

###
MAX_DISCOVERY_RETRIES = 10    # MAX tries at discovery before giving up
GROUP_PATH = "./groupCA/"     # directory storing discovery info
CA_NAME = "root-ca.crt"       # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host" # stores GGC host address
# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
discoveryInfoProvider = DiscoveryInfoProvider()

def convertImageToBase64():
 with open(image_name, "rb") as image_file:
  encoded = base64.b64encode(image_file.read())
  return encoded

def getTopic_name():
 file = open(topic_publish_file,"r")
 return file.readline()

def greengrassPublisher_run():
 topic_name = getTopic_name()
 encoded = convertImageToBase64()
 publishEncodedImage(encoded, topic_name)

def publishEncodedImage(encoded, topic_name):
 topic_name = getTopic_name()
 end = packet_size
 start = 0
 length = len(encoded)
 picId = random.randint(1,99999)
 file = open("./logs/"+str(picId)+".log","w")
 file.write("encoded >>>")
 pos = 0
 print("encoded >>>")
 print(encoded)
 file.write(str(encoded))
 file.write("\n")
 print("encoded length >>>")
 file.write("encoded length >>>")
 file.write(str(length))
 file.write("\n")
 print(length)
 no_of_packets = math.ceil(length/packet_size) + 1.0
 file.write("no_of_packets >>>")
 file.write(str(no_of_packets))
 file.write("\n")
 print(no_of_packets)
 while start <= length:
  data = {"data": encoded[start:end], "pic_id":picId, "pos": pos, "size": int(no_of_packets), "encoded_length": length}
  print("#########")
  print(pos)
  file.write("#########")
  file.write("\n")
  file.write("pos >>>")
  file.write(str(pos))
  file.write("\n")
  print(start)
  file.write("start >>>")
  file.write(str(start))
  file.write("\n")
  print(end)
  file.write("end >>>")
  file.write(str(end))
  file.write("\n")
  payload = json.JSONEncoder().encode(data)
  message = {}
  message['message'] = payload
  message['sequence'] = pos
  messageJson = json.dumps(message)
  file.write("messageJson >>>")
  file.write(str(messageJson))
  file.write("\n")
  print("message = " + messageJson)
  print("topic = " + topic_name)
  print("Before publish...")
  publish(topic_name,messageJson)
  #os.system("python basicDiscovery.py --endpoint a2ajf9aodn4yyh-ats.iot.us-east-1.amazonaws.com  --rootCA root-ca-cert.pem --cert 04c805e1ed.cert.pem --key 04c805e1ed.private.key --thingName Prabhakar_laptop --topic 'realsense/take/image' --mode publish --message '"+payload+"'")
  print("After publish")
  end += packet_size
  start += packet_size
  pos = pos +1
 time.sleep(5)
 file.close()
 #myAWSIoTMQTTClient.disconnect() # -- stop client

def publish(topic_name,payload):
 myAWSIoTMQTTClient.publish("realsense/take/image", payload, 0)
 #time.sleep(5)

# function does basic regex check to see if value might be an ip address
def isIpAddress(value):
    match = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}', value)
    if match:
        return True
    return False

# function reads host GGC ip address from filePath
def getGGCAddr(filePath):
    f = open(filePath, "r")
    return f.readline()

# Used to discover GGC group CA and end point. After discovering it persists in GROUP_PATH
def discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId):
    # Progressive back off core
    backOffCore = ProgressiveBackOffCore()

    # Discover GGCs
    #discoveryInfoProvider = DiscoveryInfoProvider()
    discoveryInfoProvider.configureEndpoint(host)
    discoveryInfoProvider.configureCredentials(iotCAPath, certificatePath, privateKeyPath)
    discoveryInfoProvider.configureTimeout(10)  # 10 sec
    print("Iot end point: " + host)
    print("Iot CA Path: " + iotCAPath)
    print("GGAD cert path: " + certificatePath)
    print("GGAD private key path: " + privateKeyPath)
    print("GGAD thing name : " + clientId)
    retryCount = MAX_DISCOVERY_RETRIES
    discovered = False
    groupCA = None
    coreInfo = None
    while retryCount != 0:
        try:
            discoveryInfo = discoveryInfoProvider.discover(clientId)
            caList = discoveryInfo.getAllCas()
            coreList = discoveryInfo.getAllCores()

            # In this example we only have one core
            # So we pick the first ca and core info
            groupId, ca = caList[0]
            coreInfo = coreList[0]
            print("Discovered GGC: " + coreInfo.coreThingArn + " from Group: " + groupId)
            hostAddr = ""

            # In this example Ip detector lambda is turned on which reports
            # the GGC hostAddr to the CIS (Connectivity Information Service) that stores the
            # connectivity information for the AWS Greengrass core associated with your group.
            # This is the information used by discovery and the list of host addresses
            # could be outdated or wrong and you would normally want to
            # validate it in a better way.
            # For simplicity, we will assume the first host address that looks like an ip
            # is the right one to connect to GGC.
            # Note: this can also be set manually via the update-connectivity-info CLI
            for addr in coreInfo.connectivityInfoList:
                hostAddr = addr.host
                if isIpAddress(hostAddr):
                    break

            print("Discovered GGC Host Address: " + hostAddr)

            print("Now we persist the connectivity/identity information...")
            groupCA = GROUP_PATH + CA_NAME
            ggcHostPath = GROUP_PATH + GGC_ADDR_NAME
            if not os.path.exists(GROUP_PATH):
                os.makedirs(GROUP_PATH)
            groupCAFile = open(groupCA, "w")
            groupCAFile.write(ca)
            groupCAFile.close()
            groupHostFile = open(ggcHostPath, "w")
            groupHostFile.write(hostAddr)
            groupHostFile.close()

            discovered = True
            print("Now proceed to the connecting flow...")
            break
        except DiscoveryInvalidRequestException as e:
            print("Invalid discovery request detected!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            print("Stopping...")
            break
        except BaseException as e:
            print("Error in discovery!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            retryCount -= 1
            print("\n"+str(retryCount) + "/" + str(MAX_DISCOVERY_RETRIES) + " retries left\n")
            print("Backing off...\n")
            backOffCore.backOff()

    if not discovered:
        print("Discovery failed after " + str(MAX_DISCOVERY_RETRIES) + " retries. Exiting...\n")
        sys.exit(-1)


# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="Hello World!",
                    help="Message to publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
iotCAPath = rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
port = args.port
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Port defaults
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Run Discovery service to check which GGC to connect to, if it hasn't been run already
# Discovery talks with the IoT cloud to get the GGC CA cert and ip address

if not os.path.isfile('./groupCA/root-ca.crt'):
    discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId)
else:
    discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId)
    #print("Greengrass core has already been discovered.")

# read GGC Host Address from file
ggcAddrPath = GROUP_PATH + GGC_ADDR_NAME
rootCAPath = GROUP_PATH + CA_NAME
ggcAddr = getGGCAddr(ggcAddrPath)
print("GGC Host Address: " + ggcAddr)
print("GGC Group CA Path: " + rootCAPath)
print("Private Key of Prabhakar_laptop thing Path: " + privateKeyPath)
print("Certificate of Prabhakar_laptop thing Path: " + certificatePath)
print("Client ID(thing name for Prabhakar_laptop): " + clientId)

if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

#myAWSIoTMQTTClient._tls_ca_certs=None
discoveryInfo = discoveryInfoProvider.discover(thingName)
caList = discoveryInfo.getAllCas()
coreList = discoveryInfo.getAllCores()

# We only pick the first ca and core info
groupId, ca = caList[0]
coreInfo = coreList[0]

connected = False
for connectivityInfo in coreInfo.connectivityInfoList:
    currentHost = connectivityInfo.host
    currentPort = connectivityInfo.port
    print("Trying to connect to core at %s:%d" % (currentHost, currentPort))
    myAWSIoTMQTTClient.configureEndpoint(currentHost, currentPort)
    try:
        print("Before MQTTClient connect...")
        myAWSIoTMQTTClient.connect()
        print("After MQTTClient connect !")
        connected = True
        break
    except BaseException as e:
        print("Error in connect!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % e.message)

if not connected:
    print("Cannot connect to core %s. Exiting..." % coreInfo.coreThingArn)
    sys.exit(-2)

# Connect and subscribe to AWS IoT -- Subscribe is Not supported !
#if args.mode == 'both' or args.mode == 'subscribe':
#    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(3)

# Publish to the same topic in a loop forever
#loopCount = 0
#while True:
#    if args.mode == 'both' or args.mode == 'publish':
#        message = {}
#        message['message'] = args.message
#        message['sequence'] = loopCount
#        messageJson = json.dumps(message)
#        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
#        if args.mode == 'publish':
#            print('Published topic %s: %s\n' % (topic, messageJson))
#        loopCount += 1

greengrassPublisher_run()

