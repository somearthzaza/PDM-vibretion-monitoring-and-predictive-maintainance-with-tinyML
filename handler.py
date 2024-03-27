
import streamlit as st
import json
import paho.mqtt.client as mqtt
import random
from streamlit_server_state import server_state, server_state_lock , no_rerun
import ble_func
import time

transection_id = 0
status = True

def onConnect(key,host,port,pi_id ):
    with no_rerun:
        try:
            if server_state["ble"]:
                server_state["ble"][key].connect()
                thread = ble_func.DeviceThread(server_state["ble"][key] , ip_addr = host, port =  port ,pi_id = pi_id)
                thread.start()
                server_state["select_device"][key] = thread
        except Exception as e:
            print(e)
        


def on_disconnect(key):
    with no_rerun:
        if server_state["select_device"]:
            server_state["select_device"][key].stop()
            del server_state["select_device"][key]



def check_pi(pi_id,pi_name,Factory_name,ip,port):
    global mqtt
    global json
    global random
    global transection_id
    global status
    global time 
    status = True
    transection_id = random.randint(1,1000)
    client = mqtt.Client()
    topic = "pi_data"
    try:
        client.connect(ip,int(port),60)
        package = json.dumps({"pi_id":pi_id,"pi_name":pi_name,"factory":Factory_name , "transection_id":transection_id})
        client.publish("pi_data",package)
        client.subscribe("pi_data_response")
        timestamp = time.time()

        while(status):
            client.on_message = on_message
            client.loop_start()

            if(time.time() - timestamp > 10):
                st.error("CONNECTION TIMEOUT: can't connect to mqtt server or server not response")
                return False
            

                
            if (status == False):
                st.success("Connected to server")
                client.loop_stop()
                print("loop stop")
                return True
            

    except Exception as e:
        st.error(f"Can't connect to server Error:{e} ")
        return False




def on_message(client, userdata, msg ):
    global json
    global transection_id
    global status
    msg = json.loads(msg.payload)
    print(msg)
    if msg["transection_id"] == transection_id:
        if msg["status"] == "success":
            status = False
        else:
            status = False





