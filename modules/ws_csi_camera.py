# MIT License
# Copyright (c) 2019,2020 JetsonHacks
# See license in root folder

# CSI_Camera is a class which encapsulates an OpenCV VideoCapture element
# The VideoCapture element is initialized via a GStreamer pipeline
# The camera is read in a separate thread

# The class also tracks how many frames/sec are grabbed in the thread from the camera, and
# how many frames/sec are read by the outside program. Both of these can be displayed on 
# the image as 'frames grabbed' and 'frames read' respectively. Frames 'grabbed' are closest
# to the camera's actual framerate. Frames 'read' will be slower, depending upon how much 
# processing per frame is performed in the calling program.

# Modified to ws_csi_camera.py 12/23/20 by WSmith to get everything associated with the
# CSI camera in one place, and simplify the frame-rate estimates. 

import cv2
import threading
from time import time

# WS mods/additions

# For 3264x2464 mode 0: 1/4 scale
DISP_W_M0_one_quarter = 816
DISP_H_M0_one_quarter = 616

# For 3264x2464 mode 0: 1/8 scale
DISP_W_M0_one_eighth = 408
DISP_H_M0_one_eighth = 308

# For 3264x1848 mode 1: 1/4 scale
DISP_W_M1_one_quarter = 816
DISP_H_M1_one_quarter = 462

# For 3264x1848 mode 1: 1/8 scale
DISP_W_M1_one_eighth = 408
DISP_H_M1_one_eighth = 231

# For 1920x1080 mode 2: 1/2 scale
DISP_W_M2_one_half = 960
DISP_H_M2_one_half = 540

# For 1920x1080 mode 2: 1/4 scale
DISP_W_M2_one_quarter = 480
DISP_H_M2_one_quarter = 270

# for 1280x720 modes 3,4: 1/2 scale
DISP_W_M3_M4_one_half = 640
DISP_H_M3_M4_one_half = 360

# for 1280x720 modes 3,4: 1/4 scale
DISP_W_M3_M4_one_quarter = 320
DISP_H_M3_M4_one_quarter = 180

# 3264x2464, 21 fps  4:3 ratio
S_MODE_0_3264_2464_21 = 0
# 3264x1848, 28 fps 16:9 ratio
S_MODE_1_3264_1848_28 = 1
# 1920x1080, 30 fps 16:9 ratio
S_MODE_2_1920_1080_30 = 2
# 1280x720,  60 fps 16:9 ratio
S_MODE_3_1280_720_60  = 3
# 1280x720, 120 fps 16:9 ratio
S_MODE_4_1280_720_120 = 4


class CSI_Camera:

    def __init__ (self, display_fps=True, alpha=0.95):

        # OpenCV video capture element
        self.display_fps = display_fps
        self.video_capture = None
        # The last captured image from the camera
        self.frame = None
        self.grabbed = False
        # The thread where the video capture runs
        self.read_thread = None
        self.read_lock = threading.Lock()
        self.running = False
        self.font_face = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = .6             # for FPS text size
        self.color = (255,255,255) # for FPS text color
        self.last_grab = time()
        self.last_time = time()
        self.fps       = 0         # grabbed frames/sec in camera thread
        self.FRS       = 0         # frames/sec read by external program
        self.alpha     = alpha     # smoothing factor for estimating fps and FRS
        # explicitly set the correct framerate per mode or there can be trouble
        self.framerate = {0:21, 1:28, 2:30, 3:60, 4:120}
 
    def open(self, gstreamer_pipeline_string):
        try:
            self.video_capture = cv2.VideoCapture(gstreamer_pipeline_string, 
                                                  cv2.CAP_GSTREAMER)
            
        except RuntimeError:
            self.video_capture = None
            print("Unable to open camera")
            print("Pipeline: " + gstreamer_pipeline_string)
            return
        # Grab the first frame to start the video capturing
        self.grabbed, self.frame = self.video_capture.read()

    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None
        # create a thread to read the camera image
        if self.video_capture != None:
            self.running=True
            self.read_thread = threading.Thread(target=self.updateCamera)
            self.read_thread.start()
        return self

    def stop(self):
        self.running=False
        self.read_thread.join()

    def updateCamera(self):
        # This is the thread to read images from the camera
        while self.running:
            try:
                grabbed, frame = self.video_capture.read()
                with self.read_lock:
                    self.grabbed = grabbed
                    self.frame   = frame
                    dt           = time() - self.last_grab
                    self.last_grab = time()
                    # estimate grabbing rate
                    self.fps = self.alpha * self.fps + (1 - self.alpha) / dt
            except RuntimeError:
                print("Could not read image from camera")
        
    def read(self):
        with self.read_lock:
            frame   = self.frame.copy()
            grabbed = self.grabbed
            dt      = time() - self.last_time
            self.last_time = time()
        if self.display_fps:
            # estimate reading rate
            self.FRS = self.alpha * self.FRS + (1 - self.alpha) / dt
            txt = "Frames Read/   Sec: {:3.1f}".format(self.FRS)
            cv2.putText(frame, txt, (10,20), self.font_face, self.scale, self.color, 1, cv2.LINE_AA)
            txt = "Frames Grabbed/Sec: {:3.1f}".format(self.fps)
            cv2.putText(frame, txt, (10,50), self.font_face, self.scale, self.color, 1, cv2.LINE_AA)
        return grabbed, frame

    def release(self):
        if self.video_capture != None:
            self.video_capture.release()
            self.video_capture = None
        # kill the thread
        if self.read_thread != None:
            self.read_thread.join()

    @property
    def gstreamer_pipeline(self):
        return self._gstreamer_pipeline

    # WS mod: Important to explicitly set the framerate appropriately for the sensor mode. 
    #         If the framerate is too fast for the sensor mode, the program can core dump. If
    #         the framerate is too slow for the sensor mode, the sensor-mode's framerate
    #         will be overridden and slower than desired. To get around this, the framerate is
    #         set using a dictionary that explicitly maps sensor mode to framerate. 

    def create_gstreamer_pipeline(self, sensor_id=0, sensor_mode=3, display_width=1280,
                                  display_height=720, flip_method=0):

        self._gstreamer_pipeline = (
            "nvarguscamerasrc sensor-id=%d sensor-mode=%d ! "
            "video/x-raw(memory:NVMM), "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (sensor_id, sensor_mode, self.framerate[sensor_mode], flip_method, 
               display_width, display_height)
        )


    
