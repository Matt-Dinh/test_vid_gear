"""_summary_
    Read metadata of all streamings from files, process and export to multiple clients.

"""

# import necessary libs
import threading
import socket
import json
import argparse
import uvicorn
import asyncio
import cv2
from vidgear.gears.asyncio import WebGear
from vidgear.gears.asyncio.helper import reducer



def gen_streaming_server(cam_id, host, port, width, height):
    
    # set default location to '/home/foo/foo1'
    options = {"custom_data_location": "."}
    # initialize WebGear app without any source
    web = WebGear(logging=True, **options)

    # create your own custom frame producer
    async def my_frame_producer():

        # !!! define your own video source here !!!
        # Open any video stream such as live webcam
        # video stream on first index(i.e. 0) device
        stream = cv2.VideoCapture(cam_id)
        # loop over frames
        while True:
            # read frame from provided source
            (grabbed, frame) = stream.read()
            # break if NoneType
            if not grabbed:
                break

            # do something with your OpenCV frame here

            # reducer frames size if you want more performance otherwise comment this line
            # reduce frame by 30%
            frame = await reducer(frame, percentage=30, interpolation=cv2.INTER_AREA)

            # resize frames
            frame = cv2.resize(frame, (width, height),
                               interpolation=cv2.INTER_AREA)

            # handle JPEG encoding
            encodedImage = cv2.imencode(".jpg", frame)[1].tobytes()
            # yield frame in byte format
            yield (b"--frame\r\nContent-Type:image/jpeg\r\n\r\n" + encodedImage + b"\r\n")
            await asyncio.sleep(0)
        # close stream
        stream.release()

    # add your custom frame producer to config
    web.config["generator"] = my_frame_producer

    # run this app on Uvicorn server at address http://localhost:8000/
    uvicorn.run(web(), host=host, port=port)

    # close app safely
    web.shutdown() 


if __name__ == "__main__":
    # Python Program to Get IP Address
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    
    parser = argparse.ArgumentParser(
                    prog = 'StreamingProgram',
                    description = 'Export Motion Jmpeg to multiple clients')
    parser.add_argument('--host', type=str, default=IPAddr, help='Host IP to public')           
    parser.add_argument('--source', type=str, default='streams_meta.json', help='Metadata of all streaming urls')           
    args = parser.parse_args()
    # print(args.source)
    source, host = args.source, args.host
    
    with open(source, 'r') as f:
        factories = json.load(f)
    
    for factory_id in factories.keys():
        for cam_id, info in factories[factory_id].items():
            rtsp_stream, host, port, width, height = info['rtsp_stream'], host, info['port'], info['width'], info['height']
            # creating thread
            t = threading.Thread(target=gen_streaming_server, args=(rtsp_stream, host, port, width, height))
            # starting thread
            t.start()
            

#compile exe command
# python -m PyInstaller --paths /home/becamex/anaconda3/envs/vid_gear/lib/python3.10/site-packages --onefile streaming.py --hidden-import simplejpeg