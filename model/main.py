import sqlite3
from model import face_extract as fe
import cv2
import pickle
import numpy as np
from scipy import spatial
import scipy.misc
import matplotlib.pyplot as plt
import time	
import json
import sys

#Returns vector embedding of image, given a path to an image with faces
def get_vec(path):
  cap = cv2.VideoCapture(path)
  has_frame, frame = cap.read()
  cap.release()
  ex = fe.face_extract(frame)
  print(ex)
  return ex 

#COnverts vec embedding to string to be stored in SQLite DB
def vec2str(vec):
  return ''.join(str(x) for x in vec).replace("[ ", "[").replace("  ", ",").replace(" ", ",").replace("\n", ",").replace(",,", ",").replace(",]", "]")

def str2vec(str):
  return [float(x) for x in np.asarray(str.replace("[", "").replace("]", "").split(","))]

def cos_distance(vec1, vec2):
  return 1 - spatial.distance.cosine(vec1, vec2)

def init_db():
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  conn.execute('''CREATE TABLE IF NOT EXISTS FACEVEC
  (ID INT PRIMARY KEY     NOT NULL,
  NAME           TEXT    NOT NULL,
  PHONE           TEXT    NOT NULL,
  EMAIL           TEXT    NOT NULL,
  AUTH           TEXT    NOT NULL,
  IMG           TEXT    NOT NULL,
  VEC           TEXT    NOT NULL
  );''')
  conn.close()

#Registers a person, to be tracked using facial recognition
def register_new_face(path, name, phone, email, auth):
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  max_id = conn.execute("SELECT MAX(ID) FROM FACEVEC").fetchone()[0]
  if max_id == None:
    id = 1024
  else:
    id = max_id + 1;
  vec = get_vec(path)
  conn.execute("INSERT INTO FACEVEC (ID,NAME,PHONE,EMAIL,AUTH,IMG,VEC) VALUES (" + str(id) + ", '" + str(name) + "', '" + str(phone) + "', '" + str(email) + "', '" + str(auth) + "', '" + str(path) + "', '" + vec2str(vec) + "');")
  conn.close()
  return id

#Update data - Reference Image, Name, Phone, etc
def update_face(path, id, name, phone, email, auth):
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  vec = get_vec(path)
  conn.execute("UPDATE FACEVEC SET  NAME='" + str(name) + "', PHONE='" + str(phone) + "', EMAIL='" + str(email) + "', AUTH='" + str(auth) + "', IMG='" + str(path) + "', VEC='" + vec2str(vec) + "' WHERE ID=" + str(id) + ";")
  conn.close()

def update_face_without_image(id, name, phone, email, auth):
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  conn.execute("UPDATE FACEVEC SET  NAME='" + str(name) + "', PHONE='" + str(phone) + "', EMAIL='" + str(email) + "', AUTH='" + str(auth) + "' WHERE ID=" + str(id) + ";")
  conn.close()

def delete_face(id):
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  conn.execute("DELETE FROM FACEVEC WHERE ID = " + str(id) + " ;")
  conn.close()

def clear_db():
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  conn.execute("DELETE FROM FACEVEC;")
  conn.close()

def c_replace(res, old_id, new_id, new_name):
  new_res = []
  for r in res:
    (x, y) = r
    if(x == old_id):
      new_res.append((new_id,new_name))
    else:
      new_res.append(r)
  return new_res


#Add row in SQLite Table mainatined for each person's movement logs
def add_log(mem_id, time, camera_id):
  conn = sqlite3.connect('log.db', isolation_level=None,  check_same_thread=False)
  print("CREATE TABLE IF NOT EXISTS {}(TIME TEXT PRIMARY KEY     NOT NULL, CAMID           TEXT    NOT NULL);".format("U" + str(mem_id)))
  conn.execute("CREATE TABLE IF NOT EXISTS {}(TIME TEXT PRIMARY KEY     NOT NULL, CAMID           TEXT    NOT NULL);".format("U" + str(mem_id)))
  conn.execute("INSERT INTO {} (TIME,CAMID) VALUES ('{}', '{}');".format("U" + str(mem_id), str(time), str(camera_id)))
  conn.close()

#Get authentication Status of a member, given their ID
def get_auth(id):
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  auth = conn.execute("SELECT AUTH from FACEVEC WHERE ID='{}'".format(str(id))).fetchone()
  return auth

#Get log as array from SQLite
def get_log(id):
  c = sqlite3.connect('log.db')
  c.row_factory = sqlite3.Row
  cur = c.cursor()
  cur.execute("CREATE TABLE IF NOT EXISTS {}(TIME TEXT PRIMARY KEY     NOT NULL, CAMID           TEXT    NOT NULL);".format("U" + str(id)))
  cur.execute("SELECT * from {}".format("U" + str(id)))
  test = cur.fetchall()
  return test


#Perform vector search on entire databse and return closest match to vector obtained from live stream data from camera
def search(vecs):
  results = []
  acc = {}
  print("faces: ", len(vecs))
  for vec in vecs:
    THRESHOLD = 0.85
    conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
    res =	{
      "id": 0,
      "name": ""
    }
    cursor = conn.execute("SELECT id, name, VEC from FACEVEC")
    max_d = 0
    c=[]
    for row in cursor:
      c.append(row)
    for row in c:
        _temp = cos_distance(vec, str2vec(row[2]))
        if _temp > max_d:
          if (row[0], row[1]) in results:
            if(_temp > acc[row[0]]):
              c.append(row)
              acc[row[0]] = _temp
            else:
              pass
          else:
            res["id"] = row[0]
            res["name"] = row[1]
            acc[row[0]] = _temp
            max_d = _temp  
            
    conn.close()
    print("confience: ", max_d)
    if(max_d >= THRESHOLD):
      results.append((res["id"], res["name"]))       
    else:
      results.append(("0", "unknown"))
  return(results)


#For testing at initial stage before UI implimentation. Not required anymore
def push_dummy_data():

  init_db()
  register_new_face("./samples/1.jpg", "arjun s", "9080151434", "arjun.santhoshkumar@gmail.com", "True")
  register_new_face("./samples/ob.jpg", "obama", "123213123", "obama@us.gov", "True")
  register_new_face("./samples/s1.jpg", "steve", "11111111", "steve@apple.com", "True")

#Get all rows from SQlite FaceVec Table
def get_p():
  conn = sqlite3.connect('facevec.db', isolation_level=None,  check_same_thread=False)
  #cursor = conn.execute("SELECT id, name, phone, email, auth from FACEVEC")
  cursor = conn.execute("SELECT id, name, phone, email, auth, img from FACEVEC")
  items = []
  for row in cursor:
    items.append({"id": row[0],
    "name": row[1],
    "phone": row[2],
    "email": row[3],
    "auth": row[4],
    "img": row[5]
    })
  conn.close()
  return json.dumps(items)
    
  
