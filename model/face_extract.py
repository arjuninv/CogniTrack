import argparse
import sys
import os
import matplotlib.pyplot as plt
from keras.models import model_from_json
from keras.applications.imagenet_utils import preprocess_input
from keras.preprocessing.image import load_img
from scipy import spatial
import scipy.misc
import cv2

import datetime
import numpy as np
import cv2

CONF_THRESHOLD = 0.5
NMS_THRESHOLD = 0.4
IMG_WIDTH = 416
IMG_HEIGHT = 416

COLOR_BLUE = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (0, 0, 0)


def get_outputs_names(net):
    layers_names = net.getLayerNames()
    return [layers_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

def post_process(frame, outs, conf_threshold, nms_threshold):
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    confidences = []
    boxes = []
    final_boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_threshold:
                center_x = int(detection[0] * frame_width)
                center_y = int(detection[1] * frame_height)
                width = int(detection[2] * frame_width)
                height = int(detection[3] * frame_height)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])


    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold,
                               nms_threshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        final_boxes.append(box)

    return final_boxes


class FPS:
    def __init__(self):
        self._start = None
        self._end = None
        self._num_frames = 0

    def start(self):
        self._start = datetime.datetime.now()
        return self

    def stop(self):
        self._end = datetime.datetime.now()

    def update(self):
        self._num_frames += 1

    def elapsed(self):
        return (self._end - self._start).total_seconds()

    def fps(self):
        return self._num_frames / self.elapsed()


model_cfg = './model/cfg/yolov3-face.cfg'
model_weights = './model/model-weights/yolov3-wider_16000.weights'
output_dir = 'outputs/'

model = model_from_json(open("./model/faceNet/facenet_model.json", "r").read())
model.load_weights('./model/faceNet/facenet_weights.h5')
model._make_predict_function()


def resizeAndPad(img, size, padColor=0):
    h, w = img.shape[:2]
    sh, sw = size
    if h > sh or w > sw: 
        interp = cv2.INTER_AREA
    else: 
        interp = cv2.INTER_CUBIC
    if h!= 0:
        aspect = w/h
    else:
        aspect = 1
    if aspect > 1:
        new_w = sw
        new_h = np.round(new_w/aspect).astype(int)
        pad_vert = (sh-new_h)/2
        pad_top, pad_bot = np.floor(pad_vert).astype(int), np.ceil(pad_vert).astype(int)
        pad_left, pad_right = 0, 0
    elif aspect < 1:
        new_h = sh
        new_w = np.round(new_h*aspect).astype(int)
        pad_horz = (sw-new_w)/2
        pad_left, pad_right = np.floor(pad_horz).astype(int), np.ceil(pad_horz).astype(int)
        pad_top, pad_bot = 0, 0
    else:
        new_h, new_w = sh, sw
        pad_left, pad_right, pad_top, pad_bot = 0, 0, 0, 0
    if len(img.shape) is 3 and not isinstance(padColor, (list, tuple, np.ndarray)): # color image but only one color provided
        padColor = [padColor]*3
    if new_h == 0 or new_w == 0:
        return img
    scaled_img = cv2.resize(img, (new_w, new_h), interpolation=interp)
    scaled_img = cv2.copyMakeBorder(scaled_img, pad_top, pad_bot, pad_left, pad_right, borderType=cv2.BORDER_CONSTANT, value=padColor)
    return scaled_img


def load_img(frame1):
    frame1 = np.asarray(frame1, dtype=np.float32)
    frame1 = resizeAndPad(frame1, (160,160))
    frame1 = cv2.resize(frame1,(160, 160),  interpolation=cv2.INTER_AREA)
    s = frame1.shape
    frame1.resize(1, s[0], s[1], s[2])
    return frame1

def cos_distance(vec1, vec2):
    return 1 - spatial.distance.cosine(vec1, vec2)


def l2_normalize(x):
    return x / np.sqrt(np.sum(np.multiply(x, x)))   


net = cv2.dnn.readNetFromDarknet(model_cfg, model_weights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

#return a list of face bounded parts of frames, given a whole frame
def face_extract(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    blob = cv2.dnn.blobFromImage(frame, 1 / 255, (416, 416), [0, 0, 0], 1, crop=False)
    net.setInput(blob)
    outs = net.forward(get_outputs_names(net))
    faces = post_process(frame, outs, CONF_THRESHOLD, NMS_THRESHOLD)

    res = []
    for face in faces:
        cropped = frame[face[1]:face[1] + face[3] , face[0]:face[0] + face[2], :]
        print("cropped shape: ", cropped.shape)
        h, w = cropped.shape[:2]
        if(w == 0 or h==0):
            return res
        vec = l2_normalize(model.predict(load_img(cropped)))
        res.extend(vec)
    return res

