# grab_frame_from_video.py
# WSmith 12/24/20

import cv2
import os

def grab_frame(dest, base, suffix='jpg', dispW=640, dispH=480):

    cam = cv2.VideoCapture(1)  # webcam for now

    num = 0

    while True:

        val, frame = cam.read()
        frame = cv2.resize(frame, (dispW, dispH))
        cv2.imshow('camera resized to {} x {}'.format(dispW, dispH), frame)

        key = cv2.waitKey(5)

        if key == ord('s'): # save image
            nam = '{}_{}.{}'.format(base, num, suffix)
            fname = os.path.join(dest, nam)
            #print(fname)
            cv2.imwrite(filename=fname, img=frame)
            num += 1

        if key == ord('q'): # quit
            break
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":

    destination = '/home/smithw/Devel/jetson_nano/pyPro/faceRecognizer/demoImages/known/'
    base_name = 'WS'
    grab_frame(destination, base_name)