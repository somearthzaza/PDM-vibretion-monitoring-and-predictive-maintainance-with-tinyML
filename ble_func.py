from __future__ import print_function
import re
import paho.mqtt.client as mqtt
import sys
import os
import time
import json
import threading
import streamlit as st
import ble_mqtt_multi
import math
from datetime import datetime
import pytz
from abc import abstractmethod
from my_manager import ManagerListener
from my_manager import Manager
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features.audio.adpcm.feature_audio_adpcm import FeatureAudioADPCM
from blue_st_sdk.features.audio.adpcm.feature_audio_adpcm_sync import FeatureAudioADPCMSync


from configparser import ConfigParser



class MyManagerListener(ManagerListener):

    #
    # This method is called whenever a discovery process starts or stops.
    #
    # @param manager Manager instance that starts/stops the process.
    # @param enabled True if a new discovery starts, False otherwise.
    #
    def on_discovery_change(self, manager, enabled):
        print('Discovery %s.' % ('started' if enabled else 'stopped'))
        if not enabled:
            print()

    #
    # This method is called whenever a new node is discovered.
    #
    # @param manager Manager instance that discovers the node.
    # @param node    New node discovered.
    #
    def on_node_discovered(self, manager, node):
        print('New device discovered: %s.' % (node.get_name()))


#global variables


SCANNING_TIME_s = 5 #seconds

topic = "sensor"
NOTIFICATIONS = 20


manager = Manager.instance()
manager_listener = MyManagerListener()
manager.add_listener(manager_listener)


class MyFeatureListener(FeatureListener):
    def __init__(self , host , port,m_id ="",description = "" ,tag = ""  ):
        try:
            self.description = "24v withload (new) broken in demo"
            self.tag = tag
            self.m_id = m_id
            self._client = mqtt.Client()
            print(host,port)
            self._client.connect(host,int(port),60)
        except Exception as e:
            st.write("error to connect to mqtt")
           
        
    def on_update(self, feature, sample):
        self._client.loop_start()
        sensorValue = str(feature)
        sensorValue = re.findall(r'-?\d+', sensorValue)
        sensorValue = [int(x) for x in sensorValue]
        sqr = math.sqrt(sensorValue[1]**2 + sensorValue[2]**2 + sensorValue[3]**2)
        print(f'X = {sensorValue[1]} Y = {sensorValue[2]} Z = {sensorValue[3]} G = {sqr}')
        timestamp = datetime.now(pytz.timezone('Asia/Jakarta'))
        json_data = {
            "tag": feature.get_parent_node().get_tag(),
            "x": sensorValue[1],
            "y": sensorValue[2],
            "z": sensorValue[3],
            "timestamp": str(timestamp),
            "g":sqr,
            "tag": self.tag,
            "sensor_name": feature.get_parent_node().get_name(),
            "description": self.description, 
            "m_id": 1
        }
        json_data = json.dumps(json_data, indent=4)
        result = self._client.publish(topic, json_data)
        status = result[0]
        self._client.loop_stop()


class MyFeatureListener2(FeatureListener):
    def __init__(self , host , port,tag):
        try:
            self.tag = tag
            self._client = mqtt.Client()
            self._client.connect(host,int(port),60)
        except Exception as e:
            st.write("error to connect to mqtt")
           
        
    def on_update(self, feature, sample):
        self._client.loop_start()
        rawData = str(feature)
        timestamp = datetime.now(pytz.timezone('Asia/Jakarta'))
        print(rawData)
        rawData = re.findall(r'-?\d+', rawData)
        cvtData = [int(x) for x in rawData]
        predictValue = cvtData[2]
        json_data = { "tag": self.tag, "predictValue": predictValue , "timestamp":str(timestamp)} 
        print(json_data)
        json_data = json.dumps(json_data, indent=4)
        result = self._client.publish("predict", json_data)
        self._client.loop_stop()


def Scanning_ble ():
    global manager
    print(manager)
    resultdiscover = manager.discover(5)
    return resultdiscover
   

def discorver_ble():
    global manager
    manager.stop_discovery()
    manager.reset_discovery()

def start_scan():
    global manager
    manager.start_discovery()
        

def  stop_scan():
    global manager
    manager.stop_discovery()
    return get_node()

def get_node():
    global manager
    return manager.get_nodes()


def get_features(device):
    if device.is_connected():
        try:
            feature = device.get_features()
            feature = feature[5]

            feature.add_listener(MyFeatureListener())
            device.enable_notifications(feature)
            
            while True:
                if device.wait_for_notifications(0.05):
                    pass
                time.sleep(1)
        except Exception as e:
            return e


class DeviceThread (threading.Thread):
    
    def __init__(self, device,pi_id = "",port = "1883" ,ip_addr = "localhost" , description = "" , *args, **kwargs):
        super(DeviceThread, self).__init__(*args,**kwargs)
        global checkstop
        self._device = device
        self._name = self._device.get_name()
        self._ip_addr = ip_addr
        self._pi_id = pi_id
        self._tag = self._device.get_tag()
        self._port = port
        self.status = False
        self.feature = self._device.get_features()
        print(self.feature)
        self.featureAcce = self.feature[4]
        self.featurePredict = self.feature[1]
        self.listenerPredict = MyFeatureListener2(self._ip_addr , self._port ,tag = self._tag,)
        self.listenerAcce = MyFeatureListener(self._ip_addr , self._port  ,m_id = self._pi_id ,tag = self._tag , description = description)
        self.featureAcce.add_listener(self.listenerAcce)
        self.featurePredict.add_listener(self.listenerPredict)
    def run (self):
        try:
            self._device.enable_notifications(self.featureAcce)
            self._device.enable_notifications(self.featurePredict)
            while True:
                if self._device.wait_for_notifications(0.05):
                    pass
                else:
                    print("waiting for notification")
                if self.status:
                    break
                # time.sleep(0.2)
         
        except Exception as e:
            print("error")

    def _send_message(self, topic, message):
        """Send a message to a topic."""
        result = self._client.publish(topic, message)
        status = result[0]
        if status == 0:
            print(f"Send `{message}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

    def _connect(self):
        self._device.add_listener(MyNodeListener())
        print('Connecting to %s...' % (self._device.get_name()))
        if not self._device.connect():
            print('Connection failed.\n')
            return
        return True


    def stop (self):
        self.status = True
        # self._device.disable_notifications(self.feature)
        self._device.disconnect()
        self.featurePredict.remove_listener(self.listenerPredict)
        self.featureAcce.remove_listener(self.listenerAcce)
        self.join()
        
    def get_device(self):
        """Get the handled device."""
        return self._device
    
    def get_name(self):
        return self._name



class MyNodeListener(NodeListener):
    def on_connect(self, node):
        print('Device %s connected.' % (node.get_name()))

    def on_disconnect(self, node, unexpected=False):
        print('Device %s disconnected%s.' % \
            (node.get_name(), ' unexpectedly' if unexpected else ''))




