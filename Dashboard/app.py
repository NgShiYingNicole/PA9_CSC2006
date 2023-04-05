from flask import Flask, json
from flask import render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import pandas as pd

app = Flask(__name__)

'''
for int routes
@app.route('/<int:id>')
def func(id):
    print(id)
'''

@app.route('/')
@app.route('/index')
def index():
    data_json = getFarmdata()
    # Flatten data, To include farmId
    df_nested_list = pd.json_normalize(data_json, meta=['farmId'], record_path =['sensors'])
    table = df_nested_list.to_html(index=True)
    return render_template("dashboard.html",table=table)
#-----------------------------------------------------------------------------------------------------------------------#

app.config['MQTT_BROKER_URL'] = '192.168.246.252'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = ''
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 300  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your server supports TLS, set it True

# declaring mqtt routes
mqtt_farm = 'mqtt_farm' 
endpoint = 'endpoint' 

# initializing mqtt and socket
mqtt_client = Mqtt(app)
socketio = SocketIO(app)

# subscribe to topics on connect
@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully')
       mqtt_client.subscribe(mqtt_farm)
       mqtt_client.subscribe(endpoint)
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

def getFarmdata():
    data = json.loads(open('data/farmdata.json').read())
    return data['records']

def writeToDatabase(data):
    with open('data/farmdata.json', 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside records
        for farm in data["farms"]:
            file_data["records"].append(farm)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)
        return

if __name__  == "__main__":
    socketio.run(app, host='127.0.0.1', port=5000, use_reloader=True, debug=True)
  
