from flask import Flask, render_template, url_for, send_file, Response, jsonify, send_file, request
import json
import socket, threading
import sys
import os, string
import cv2
import pickle
import numpy as np
import struct
from time import sleep
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from model import main
import random
import datetime
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import time
import datetime

app = Flask(__name__)


#Initialising Firebase

cred = credentials.Certificate('cognitrack-c16c7-firebase-adminsdk-z1d49-12f0467c44.json')
default_app = firebase_admin.initialize_app(cred,  {'databaseURL': 'https://cognitrack-c16c7.firebaseio.com'})
ref = db.reference('/')
s_ref = ref.child('server')

db.reference('/').child('camera').set("")
db.reference('/').child('ip_list').set("")
db.reference('/').child('track').set("")
db.reference('/').child('camera_track').set("")

#Function to add ip of connected camera to firebase
def add_ip(ip):
    ref = db.reference('ip_list')
    cur_ip = ref.get()
    if cur_ip == None or cur_ip == "":
        ref.set(ip[0])
    else:
        if ip[0] not in cur_ip:
            print(cur_ip + "," + ip[0])
            ref.set(cur_ip + "," + ip[0])

#Function to remove ip of connected camera to firebase

def remove_ip(ip):
    ref = db.reference('ip_list')
    cur_ip = ref.get()
    if "," + str(ip[0]) in cur_ip:
        new_ip = cur_ip.replace("," + str(ip[0]), "")
    elif str(ip[0]) in cur_ip:
        new_ip = cur_ip.replace(str(ip[0]), "")
    else:
        new_ip = cur_ip
    ref.set(new_ip)


#FUnction to get ip of device
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


#ClientTread class for instantiating seperate thread for each process (ML model instance and Flask server)
def socket_init():
    class ClientThread(threading.Thread):
        global image
        def __init__(self,clientAddress,clientsocket):
            global ip_list
            threading.Thread.__init__(self)
            self.csocket = clientsocket
            self.caddr = clientAddress
            self.client_ip = clientAddress[0]
            print(self.client_ip)
            print ("New connection added: ", clientAddress)
            model_thread = threading.Thread(target=model, args=[(str(clientAddress[0]).replace(".", ""))])
            model_thread.start()
            print("clientAddress: ", clientAddress)
            add_ip(clientAddress)

        def run(self):
            print ("Connection from : ", self.caddr)
            data = b''
            payload_size = struct.calcsize("L")
            connected = True
            while connected:
                while len(data) < payload_size:
                    temp = self.csocket.recv(4096)
                    data += temp
                    if not temp:
                        connected = False
                        break
                if connected:
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("L", packed_msg_size)[0]
                    
                    while len(data) < msg_size:
                        temp = self.csocket.recv(4096)
                        data += temp
                        if not temp:
                            connected = False
                    frame_data = data[:msg_size]
                    data = data[msg_size:]
                    frame=pickle.loads(frame_data)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    cv2.imwrite("feed/" + str(self.caddr[0]).replace(".", "") + '.jpg',frame, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            remove_ip(self.caddr)
            print ("Client at ", self.caddr , " disconnected...")

    HOST= str(get_ip_address())
    s_ref.set({
    'ip': HOST
    })
    print("HOST: ",HOST)
    PORT = 8089
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    print("Server started")
    print("Waiting for client request..")
    while True:
        server.listen(10)
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.start()

#Function to stream video feed from wirelessly connected camera to Web UI
def listen(ip):
    while True:
        yield(b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + open("feed/" + ip + ".jpg", 'rb').read() + b'\r\n')
        sleep(0.1)

#Instance of ML model for each live stream socket connection from camera 
def model(img):
    m_ref = db.reference('track/')
    c_ref = db.reference('camera_track/')
    a_ref = db.reference('alert/')

    while True:
        print("model init: ", "feed/" + img + '.jpg')
        if os.path.isfile("feed/" + img + '.jpg'):
            print("running model for " + "feed/" + img + '.jpg')
            vec = main.get_vec("feed/" + img + '.jpg')
            print("in model" + img + ", vec = ", vec)
            res = main.search(vec)
            print(res)
            cam = c_ref.child(img)
            cam.set("")
            his = {}
            a_ref.set({'msg': ''})
            for face in res:
                print("auth: ", str(main.get_auth(face[0])))
                if(str(main.get_auth(face[0])) == "('False',)"):
                    print("auth fail")
                    a_ref.set({'msg': 'Unauthorised member (ID ' + str(face[0]) + ') has entered premise'})
                if(str(face) in his and his[str(face)] != img):
                    main.add_log(str(face[0]), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), img)
                    his[str(face)] = img
                mem = m_ref.child(str(face[0]))
                mem.set({
                    'current_loc': {
                    'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'cam': img
                    }
                })
                cam .child(str(face[0])).set({
                    'name': str(face[1]),
                    'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        sleep(4)


#Directives to handle url requests in flask
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/log/<id>')
def log(id):
    return render_template("log.html", test = main.get_log(id))

@app.route('/manage')
def manage():
    return render_template("manage.html")

@app.route('/stream/<ip>/frame.jpg')
def stream(ip):
    return Response(listen(ip), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/thumbnail/<ip>/frame.jpg')
def thumbnail(ip):
    return send_file("feed/" + str(ip) + ".jpg", mimetype='image/jpg')

@app.route('/register-new',methods=['POST', 'GET'])
def register_new_mem():
    if request.method=='POST':
        name=request.form['name']
        phone=request.form['phone']
        email=request.form['email']
        auth=request.form['auth']
        file = request.files['image']
        f = os.path.join("face_raw/", ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)))
        file.save(f)
        return main.register_new_face(f, name, phone, email, auth)
    else:
        return "error"

@app.route('/profile/facedata/<file>')
def profile_img(file):  
    return send_file("facedata/" + str(file), mimetype='image/jpg')

@app.route('/get-list')
def get_list():
    return main.get_p()


@app.route('/update',methods=['POST'])
def update():
    if request.method=='POST':
        if(request.form["img"] == "same_image"):
            main.update_face_without_image(request.form["id"], request.form["name"], request.form["phone"], request.form["email"], request.form["auth"])
            return "done"
        else:    
            main.update_face("facedata/" + request.form["img"], request.form["id"], request.form["name"], request.form["phone"], request.form["email"], request.form["auth"])
            return "done"
    else:
        return "error"

@app.route('/register',methods=['POST'])
def register():
    if request.method=='POST':
        main.register_new_face("facedata/" + request.form["img"], request.form["name"], request.form["phone"], request.form["email"], request.form["auth"])
        return "done"
    else:
        return "error"

@app.route('/delete',methods=['POST'])
def delete():
    if request.method=='POST':
        main.delete_face(request.form["id"])
        return "done"
    else:
        return "error"

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    UPLOADS_PATH = join(dirname(realpath(__file__)), 'facedata\\')
    if request.method == 'POST':
        if 'file' not in request.files:
            return "error"
        file = request.files['file']
        fn = secure_filename(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15)) + ".jpg")
        file.save(UPLOADS_PATH + fn)
        return fn
    return "error"


if __name__ == '__main__':
    main.init_db()
    t2 = threading.Thread(target=socket_init)
    t2.start() 
    app.run(host='0.0.0.0', threaded=True, port=30, debug=True)