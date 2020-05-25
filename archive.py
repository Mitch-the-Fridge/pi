import json
from shutil import make_archive, rmtree, move
import tempfile
import os
import cv2
from buffer import Buffer
import uuid
import requests
from collections import deque
from datetime import datetime, timedelta

# holds information about items on disk
disk_queue = deque()

# hold 20 clips at max in /dev/shm
cache_buffer = Buffer(20, lambda clip: move_to_storage(clip))

def move_to_storage(clip):
    dir_path = os.path.expanduser("~/.beer_clips")
    os.makedirs(dir_path, exist_ok=True)
    new_path = move(clip['path'], dir_path)

    clip['path'] = new_path
    disk_queue.append(clip)

def create_from_clip(clip):
    info_dict = {
        'frames': [],
        'uuid': str(uuid.uuid4()),
        'fps': 20,
    }

    for frame in clip:
        info_dict['frames'].append({
            'time': round(frame['time'].timestamp() * 1e3),
            'face_locations': frame['face_locations'],
            'current_weight': frame['current_weight'],
        })

    out = json.dumps(info_dict)

    with tempfile.TemporaryDirectory(dir="/dev/shm/") as tmpdir:
        with open(os.path.join(tmpdir, "info.json"), 'w') as f:
            f.write(out + '\n')

        i = 0
        for frame in clip:
            fname = os.path.join(tmpdir, str(i).rjust(10, '0') + ".jpg")
            cv2.imwrite(fname, frame['frame'])
            i += 1

        archive_output_path = os.path.join("/dev/shm/", str(clip[0]['time'].timestamp()))

        path = make_archive(archive_output_path, "tar", tmpdir)
        cache_buffer.add({
            'uuid': info_dict['uuid'],
            'path': path,
        })
        return path

def upload(fname):
    with open(fname, 'rb') as f:
        requests.post('http://localhost:5030/clips', data=f)

n_tries = 0
last_try_time = datetime.fromtimestamp(0) # start with low value
def try_upload_buffer():
    global last_try_time, n_tries

    backoff = max(2**n_tries, 60*10) # max backoff of 10 minutes
    if datetime.now() < last_try_time + timedelta(0, backoff):
        # too soon
        return

    # prioritize disk queue
    queue = disk_queue if len(disk_queue) > 0 else cache_buffer
    if len(queue) == 0:
        return

    file_info = queue[0]

    # TODO: async (should've used node lol)

    try:
        upload(file_info['path'])
    except Exception as e:
        n_tries += 1
        last_try_time = datetime.now()
        print("error while uploading", file_info, e, "n_tries is now", n_tries)
        return

    queue.popleft()

    try:
        os.remove(file_info['path'])
    except Exception as e:
        print("error while removing file", file_info, "error was", e)
