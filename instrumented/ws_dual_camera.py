# ws_dual_camera.py
# WSmith 12/23/20
# utilize modified module ws_csi_camera for the camera class

import cv2
import numpy as np
import ws_csi_camera as ws
from importlib import reload

#reload(ws)  # since ws is under development

def display(sensor_mode=ws.S_MODE_3_1280_720_60, 
            dispW=ws.DISP_W_M3_M4_one_half, 
            dispH=ws.DISP_H_M3_M4_one_half,
            display_fps=True):

    # at present, display the picam and a webcam: in the future, display two picams

    picam  = ws.CSI_Camera(display_fps=display_fps)
    webcam = ws.CSI_Camera(display_fps=display_fps)

    # this only needed for the picam
    picam.create_gstreamer_pipeline(sensor_id=0, sensor_mode=sensor_mode, flip_method=0,
                                    display_height=dispH, display_width=dispW)

    picam.open(picam.gstreamer_pipeline)
    webcam.open(1)

    picam.start()
    webcam.start()

    txt = "Picam on left: Sensor Mode {}, Display {} x {}".format(sensor_mode, dispW, dispH)
    cv2.namedWindow(txt, cv2.WINDOW_AUTOSIZE)

    picam.start_counting_fps()
    webcam.start_counting_fps()

    while True:

        _, imgL = picam.read()
        _, imgR = webcam.read()

        imgR = cv2.resize(imgR, (imgL.shape[1], imgL.shape[0]))
        img = np.hstack((imgL, imgR))

        cv2.imshow(txt, img)

        picam.frames_displayed  += 1
        webcam.frames_displayed += 1

        keyCode = cv2.waitKey(5) & 0xFF
        
        if keyCode == ord('q'):
            break

    picam.stop()
    webcam.stop()
    picam.release()
    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":

    display(sensor_mode=ws.S_MODE_0_3264_2464_21, 
            dispW=ws.DISP_W_M0_one_eighth, dispH=ws.DISP_H_M0_one_eighth)


