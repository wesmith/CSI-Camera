# MIT License
# Copyright (c) 2019 JetsonHacks
# See LICENSE for OpenCV license and additional information

# https://docs.opencv.org/3.3.1/d7/d8b/tutorial_py_face_detection.html
# On the Jetson Nano, OpenCV comes preinstalled
# Data files are in /usr/sharc/OpenCV

import cv2
import numpy as np
from csi_camera import CSI_Camera

show_fps = True

# Simple draw label on an image; in our case, the video frame
def draw_label(cv_image, label_text, label_position):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    color = (255,255,255)
    # You can get the size of the string with cv2.getTextSize here
    cv2.putText(cv_image, label_text, label_position, font_face, scale, color, 1, cv2.LINE_AA)

# Read a frame from the camera, and draw the FPS on the image if desired
# Return an image
def read_camera(csi_camera,display_fps):
    _ , camera_image=csi_camera.read()
    if display_fps:
        draw_label(camera_image, "Frames Displayed (PS): "+str(csi_camera.last_frames_displayed),(10,20))
        draw_label(camera_image, "Frames Read (PS): "+str(csi_camera.last_frames_read),(10,40))
    return camera_image

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


def face_detect(sensor_mode=S_MODE_3_1280_720_60,
                dispW=DISP_W_M3_M4_one_half,
                dispH=DISP_H_M3_M4_one_half):

    face_cascade = cv2.CascadeClassifier(
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
    )
    eye_cascade = cv2.CascadeClassifier(
        "/usr/share/opencv4/haarcascades/haarcascade_eye.xml"
    )
    left_camera = CSI_Camera()

    # WS mod: IMPORTANT use lowest fps = 21 as default, otherwise modes 0 or 1 crash: reboot required
    left_camera.create_gstreamer_pipeline(
            sensor_id=0,
            sensor_mode=sensor_mode,
            framerate=21,
            flip_method=0,
            display_height=dispH,
            display_width=dispW,
    )
    left_camera.open(left_camera.gstreamer_pipeline)
    left_camera.start()
    txt = "Face Detect: Sensor Mode {}, Display {} x {}".format(sensor_mode, dispW, dispH)  # WS mod
    cv2.namedWindow(txt, cv2.WINDOW_AUTOSIZE)

    if (
        not left_camera.video_capture.isOpened()
     ):
        # Cameras did not open, or no camera attached

        print("Unable to open any cameras")
        # TODO: Proper Cleanup
        SystemExit(0)
    try:
        # Start counting the number of frames read and displayed
        left_camera.start_counting_fps()
        while cv2.getWindowProperty(txt, 0) >= 0 :
            img=read_camera(left_camera,False)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                roi_gray = gray[y : y + h, x : x + w]
                roi_color = img[y : y + h, x : x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(
                        roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2
                    )
            if show_fps:
                draw_label(img, "Frames Displayed (PS): "+str(left_camera.last_frames_displayed),(10,20))
                draw_label(img, "Frames Read (PS): "+str(left_camera.last_frames_read),(10,40))
            cv2.imshow(txt, img)
            left_camera.frames_displayed += 1
            keyCode = cv2.waitKey(5) & 0xFF
            # Stop the program on the ESC key
            if keyCode == 27:
                break
    finally:
        left_camera.stop()
        left_camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    face_detect(sensor_mode=S_MODE_0_3264_2464_21,
                dispW=DISP_W_M0_one_quarter,
                dispH=DISP_H_M0_one_quarter)
