import ble_func
import time
import sys
import os
import paho.mqtt.client as mqtt
import json
import streamlit as st
import extra_streamlit_components as stx
import handler
import threading
import signal
from my_manager import ManagerListener
from my_manager import Manager
from configparser import ConfigParser
from streamlit_server_state import server_state, server_state_lock , no_rerun


with server_state_lock["ble"]:
    if "ble" not in server_state:
        server_state["ble"] = []

with server_state_lock["select_device"]:
    if "select_device" not in server_state:
        server_state["select_device"] = {}



if "confirm_pi_id" not in st.session_state:
    st.session_state.confirm_pi_id = True




if os.path.exists("config.ini") == False:
    with open("config.ini", "w") as f:
        f.write("[IP]\n")
        f.write("ip = 192.168.1.172:1883\n")
        ip_text = "192.168.1.172:1883"
        f.write("[PI_NAME]\n")
        pi_name = "ble_pi"
        f.write("name = ble_pi\n")
        f.write("[FACTORY_NAME]\n")
        Factory_name = "default"
        f.write("FACTORY = default\n")
        f.write("[ID]\n")
        pi_id = "1"
        f.write("id = 1\n")

        f.close()

elif os.path.exists("config.ini") == True:
    config_object = ConfigParser()
    config_object.read("config.ini")
    ip_addr = config_object["IP"]
    ip_text = ip_addr["ip"]
    ip_addr = ip_addr["ip"]
    ip_addr = ip_addr.split(":")
    if(len(ip_addr) == 2):     
        host = ip_addr[0]
        port = ip_addr[1]
    
    Factory_name = config_object["FACTORY_NAME"]
    Factory_name = Factory_name["FACTORY"]

    pi_name = config_object["PI_NAME"]
    pi_name = pi_name["name"]

    pi_id = config_object["ID"]
    pi_id = pi_id["id"]




st.set_page_config(page_title="BLE MQTT", page_icon=":shark:", layout="wide")
SCANNING_TIME_s = 5
st.title("BLE MQTT")

with st.container(border = True):

    st.write("Pi configuration")
    pi_id = st.text_input("Enter id of pi:", placeholder="Pi id" , value = pi_id)
    pi_name = st.text_input("Enter name of pi:", placeholder="Pi name" , value = pi_name)
    Factory = st.text_input("Enter Factory of pi:" ,placeholder="Factory name" ,value = Factory_name)
    save_pi = st.button("save pi data" ,disabled = st.session_state.confirm_pi_id != True) 
 
       

    if save_pi:
        config_object = ConfigParser()
        config_object.read("config.ini")
        config_object["PI_NAME"] = {
            "name": pi_name
        }
        config_object["FACTORY_NAME"] = {
            "FACTORY": Factory
        }
        config_object["IP"] = {
            "ip": ip_text
        }
        with open("config.ini", "w") as conf:
            config_object.write(conf)
        st.write("saved")

with st.container(border = True):
    st.write("Mqtt configuration")
    ip_addr = st.text_input("Enter ip to sending mqtt:", key="ip", placeholder="localhost:1883" , value = ip_text)
    if ip_addr:
        ip_split = ip_addr.split(":")
        print(ip_split)
        if(len(ip_addr) == 2):     
            host = ip_addr[0]
            port = ip_addr[1]
    

    if st.button("Save ip Mqtt" ,disabled = st.session_state.confirm_pi_id != True):
        config_object = ConfigParser()
        config_object.read("config.ini")
        config_object["PI_NAME"] = {
            "name": pi_name
        }
        config_object["FACTORY_NAME"] = {
            "FACTORY": Factory
        }
        config_object["IP"] = {
            "ip": ip_addr
        }
        with open("config.ini", "w") as conf:
            config_object.write(conf)
        st.write("saved")

test_connect = st.button("test connect")
result = True


if test_connect:
    result = handler.check_pi(pi_id,pi_name,Factory,host,port)
    if result:
        st.session_state.confirm_pi_id = False
    else:
        st.session_state.confirm_pi_id = True

st.write("BLE SCAN")
if st.button("Scan",disabled = st.session_state.confirm_pi_id  ): #st.session_state.confirm_pi_id
    if server_state["select_device"]:
        for i in range(len(server_state["select_device"])):
            if server_state["select_device"].is_connected():
                device.disconnect()
                server_state["select_device"][i] = None
    result = ble_func.Scanning_ble()
    if result:
        node =  ble_func.get_node()
        with no_rerun:
            server_state["ble"] = node

with no_rerun:
    if server_state["ble"]:
        cols = st.columns(len(server_state["ble"]))
        for i , x in enumerate(cols):
            x.write(server_state["ble"][i].get_name())
            if server_state["ble"][i].is_connected():
                button = x.button("Connect" , key = i , disabled = True)
                dis_button = x.button("disconnect" , key =f"disconnect_{i}" ,on_click = handler.on_disconnect , args = [i])
            else:
                print(host,port)
                button = x.button("Connect" , key =f"connect_{i}" , on_click = handler.onConnect , args = [i,host,port ,pi_id])
    else:
        st.write(" not found sensor")






