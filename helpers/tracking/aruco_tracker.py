# import the necessary packages
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import cv2
import threading


class aruco_tracker:


    def __init__(self, controller):
         tracking = False
         self.controller = controller

    def initialise_video(self):
        # initialize the video stream and allow the camera sensor to warm up
        print("[INFO] starting video stream...")
        self.vs = VideoStream(src=2).start()
        #vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)
        self.arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_100)
        
        
        

    def stop_tracking(self):
        self.tracking=False

    def start_tracking(self, trackedId):
        self.tracking=True
        self.thread = threading.Thread( 
            target=self.track, args=(trackedId,))
        #self.thread.daemon = True
        self.thread.start()

    def get_deltas(self):
        return self.deltaX,self.deltaY

    def track(self, trackedId):
        lastX=0
        lastY=0
        while self.tracking:
            
            # grab the frame from the threaded video stream and resize it to
            # have a maximum width of 800 pixels
            image = self.vs.read()
            #image = imutils.resize(image, width=800)
            # find the barcodes in the frame and decode each of the barcodes
            arucoParams = cv2.aruco.DetectorParameters_create()
            (corners, ids, rejected) = cv2.aruco.detectMarkers(image, self.arucoDict,parameters=arucoParams)
            # verify *at least* one ArUco marker was detected
            if len(corners) > 0:
                # flatten the ArUco IDs list
                ids = ids.flatten()
                # loop over the detected ArUCo corners
                for (markerCorner, markerID) in zip(corners, ids):
                    if markerID == trackedId:
                        self.tracking_tag=True
                        trackedcorners = markerCorner.reshape((4, 2))
                        (tLeft, tRight, bRight, bLeft) = trackedcorners
                        trackedX = int((tLeft[0] + bRight[0]) / 2.0)
                        trackedY = int((tLeft[1] + bRight[1]) / 2.0)
                        self.deltaX = lastX-trackedX
                        self.deltaY = lastY-trackedY
                        if ((self.deltaX) !=0 | (self.deltaY !=0) ):
                            self.controller.tracking_jog((self.deltaX/10),(self.deltaY/10))
                        print ("tracking delta {} {}".format(self.deltaX,self.deltaY))
                        lastX=trackedX
                        lastY=trackedY

            