from flask import Flask, jsonify,request, json
from flask import sessions
from flask import request
from flask import render_template
from flask import redirect, url_for
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from random import random
from threading import Lock
import pandas as pd

"""
Background Thread
"""
thread = None
thread_lock = Lock()
app = Flask(__name__)
# ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
session = {}

'''
for int routes
@app.route('/<int:id>')
def func(id):
    print(id)
'''
'''
Get current date time
'''
# def get_current_datetime():
#     now = datetime.now()
#     return now.strftime("%m/%d/%Y %H:%M:%S")

'''
Generate random sequence of dummy sensor values and send it to our clients
'''
# def background_thread():
#     print("Generating random sensor values")
#     while True:
#         dummy_sensor_value = round(random() * 100, 3)
#         socketio.emit('mqtt_message', {'value': dummy_sensor_value})
#         socketio.sleep(1)


@app.route('/')
@app.route('/index')
def index():
    data_dic = getFarmdata()
    # Flatten data, To include farmId
    df_nested_list = pd.json_normalize(data_dic, meta=['farmId'], record_path =['sensors'])
    table = df_nested_list.to_html(index=True)
    return render_template("dashboard.html",table=table)

# @app.route('/test')
# def table():
#     data_dic = getFarmdata()
#     # Flatten data, To include farmId
#     df_nested_list = pd.json_normalize(data_dic, meta=['farmId'], record_path =['sensors'])
#     table = df_nested_list.to_html(index=True)
#     return render_template("test.html",table=table)

#-----------------------------------------------------------------------------------------------------------------------#

app.config['MQTT_BROKER_URL'] = '192.168.246.252'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = ''
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 300  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your server supports TLS, set it True

# declaring mqtt routes
csc2006 = 'csc2006' 

# initializing mqtt and socket
mqtt_client = Mqtt(app)
socketio = SocketIO(app)

# """
# Decorator for connect
# """
# @socketio.on('connect')
# def connect():
#     global thread
#     print('Client connected')

#     global thread
#     with thread_lock:
#         if thread is None:
#             thread = socketio.start_background_task(background_thread)

# """
# Decorator for disconnect
# """
# @socketio.on('disconnect')
# def disconnect():
#     print('Client disconnected',  request.sid)

# subscribe to topics on connect
@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully')
       mqtt_client.subscribe(csc2006)
   else:
       print('Bad connection. Code:', rc)

# storing mqtt data in data variable for display
@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    print(message.topic)
    data = dict(topic=message.topic,payload=message.payload.decode())
    # Convert JSON string to dictionary
    data_dict = json.loads(message.payload.decode()) 
    writeToDatabase(data_dict)
    # emit a mqtt_message event to the socket containing the message data using socket.on in the html page
    socketio.emit('mqtt_message', data=data)
    # debugging purposes
    print('Received message on topic: {topic} with payload: {payload}'.format(**data))

@mqtt_client.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)
    return


# -------------- MQTT Routes --------------------------
# publishing messages to broker
# @app.route('/publish', methods=['POST'])
# def publish_message():
#    coord = request.form.get("coord")
#    mqtt_client.publish(coordfromFlask, coord)
#    return render_template('data.html')

# -------------- MQTT Routes --------------------------

def getFarmdata():
    data = json.loads(open('data/farmdata.json').read())
    return data['records']

def writeToDatabase(data):
    with open('data/farmdata.json', 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        for farm in data["farms"]:
            file_data["records"].append(farm)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)
        return

if __name__  == "__main__":
    socketio.run(app, host='127.0.0.1', port=5000, use_reloader=True, debug=True)
  
