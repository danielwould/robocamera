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
        firstTrack=True
        initialPositionX=0
        initialPositionY=0
        while self.tracking:
            xjog=0
            yjog=0
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
                        self.deltaX = (initialPositionX - trackedX)
                        self.deltaY = (initialPositionY - trackedY)
                        if (firstTrack == True):
                            #first instruction is always delta from a 0 which is a huge move
                            firstTrack = False
                            initialPositionX=trackedX
                            initialPositionY=trackedY
                        else:
                            if ((initialPositionX - trackedX) <=-10 & (initialPositionX - trackedX) >=-100):
                                #jog x towards initial position
                                xjog=0.5
                            if ((initialPositionX - trackedX) <=-100):
                                #jog x towards initial position
                                xjog=1
                            
                            if ((initialPositionX - trackedX) >=10 & (initialPositionX - trackedX) <=100 ):
                                xjog=-0.5
                            if ((initialPositionX - trackedX) >=100 ):
                                xjog=-1

                                
                            if ((initialPositionY - trackedY) <=-10 & (initialPositionY - trackedY) >=-100):
                                #jog x towards initial position
                                yjog=0.5
                            
                            if ((initialPositionY - trackedY) <=-100):
                                #jog x towards initial position
                                yjog=1

                            
                            if ((initialPositionY - trackedY) >=10 & (initialPositionY - trackedY) <=100 ):
                                yjog=-0.5
                            if ((initialPositionY - trackedY) >=100):
                                yjog=-1


                            if ((xjog !=0) | (yjog!=0)):
                                #move the opposite direction to the delta
                                self.controller.tracking_jog(xjog,yjog)
                                print ("jogging glyph back to starting location {} {}".format(self.deltaX, self.deltaY))
                        lastX=trackedX
                        lastY=trackedY

            