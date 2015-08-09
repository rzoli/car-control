import sys
import io
import socket
import struct
import time
import picamera

port=8001
import zmq
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:{0}" .format(port))
try:
    with picamera.PiCamera() as camera:
        camera.resolution = (1000,1000)
        camera.awb_mode='auto'
        camera.ISO=400
        camera.shutter_speed=10000
        # Start a preview and let the camera warm up for 2 seconds
        camera.start_preview()
        time.sleep(2)

        start = time.time()
        stream = io.BytesIO()
        ct=0
        
        for foo in camera.capture_continuous(stream, 'jpeg'):
            ct+=1
            stream.seek(0)
            socket.send(stream.read())
            print stream.tell()
            stream.seek(0)
            stream.truncate()

            if time.time()-start>int(sys.argv[1]):
                break
        print time.time()-start
finally:
    pass
print ct
