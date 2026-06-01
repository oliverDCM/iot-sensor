import paho.mqtt.client as mqtt
import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore
import json, os, time, threading

cred = credentials.Certificate("/app/firebase-key.json")
firebase_admin.initialize_app(cred)
db_firebase = firestore.client()

def conectar_db():
    while True:
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'),
                autocommit=True
            )
            return conn
        except:
            print("[DB] Esperando MariaDB...")
            time.sleep(3)

db = conectar_db()
topic = os.getenv('MQTT_TOPIC')
ultimo_dato = {}  # guarda el último estado recibido

def guardar(data):
    global db
    try:
        if not db.is_connected():
            db = conectar_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO lecturas (sensor, deteccion, estado, timestamp_esp) VALUES (%s, %s, %s, %s)",
            (data['sensor'], 1 if data['deteccion'] else 0, data['estado'], data['timestamp'])
        )
        cursor.close()

        db_firebase.collection("lecturas").add({
            "sensor":    data['sensor'],
            "deteccion": data['deteccion'],
            "estado":    data['estado'],
            "timestamp": data['timestamp'],
            "fecha":     firestore.SERVER_TIMESTAMP
        })
        print(f"[OK] {data['estado']} · {data['timestamp']}")
    except Exception as e:
        print(f"[ERROR] {e}")

def on_message(client, userdata, msg):
    global ultimo_dato
    try:
        data = json.loads(msg.payload.decode())
        ultimo_dato = data
        guardar(data)
    except Exception as e:
        print(f"[MQTT ERROR] {e}")

# Hilo que reenvía el último estado cada 30s si no llegan mensajes nuevos
def heartbeat():
    while True:
        time.sleep(30)
        if ultimo_dato:
            print("[HEARTBEAT] Reenviando último estado...")
            guardar(ultimo_dato)

threading.Thread(target=heartbeat, daemon=True).start()

client = mqtt.Client()
client.on_message = on_message
client.connect(os.getenv('MQTT_HOST'), 1883)
client.subscribe(topic)
client.loop_forever()