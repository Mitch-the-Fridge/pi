#!/usr/bin/env python3

#import face_recognition
import cv2
import numpy as np
from datetime import datetime, timedelta
from buffer import Buffer
from collections import deque
import os
from copy import copy
import archive

WEIGHT_EPS = 5
TIMEOUT = 5 # in seconds

def poll_weight():
    return 500

# with an fps we then have a "before" duration of 15 seconds
video_buffer = Buffer(300)

building = False
clip = None
previous_weight = poll_weight()
last_weight_event = None

cap = cv2.VideoCapture(0)

while True:
    archive.try_upload_buffer()

    # if enough_diff is true we will actually start the recording
    weight = poll_weight()
    weight_diff = weight - previous_weight
    enough_diff = abs(weight_diff) >= WEIGHT_EPS

    ret, frame = cap.read()
    rgb_frame = cv2.resize(frame, (0, 0), fx=.5, fy=.5)[:, :, ::-1]

    #face_locations = face_recognition.face_locations(rgb_frame)
    print(
        len(video_buffer.q),
        len(clip) if clip is not None else 0,
        building,
        #face_locations
    )

    point = {
        'time': datetime.now(),
        #'face_locations': face_locations,
        'frame': frame,
        'current_weight': weight,
    }
    if building:
        clip.append(point)
    else:
        video_buffer.add(point)

    if not building and enough_diff:
        building = True
        clip = copy(video_buffer.q)
        video_buffer.clear()
    elif building and datetime.now() >= last_weight_event + timedelta(0, TIMEOUT):
        frames = list(clip)

        clip = None
        building = False

        print("creating clip of len", len(frames))
        print(archive.create_from_clip(frames))

    previous_weight = weight
    if enough_diff:
        last_weight_event = datetime.now()
