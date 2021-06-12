# import the necessary packages
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2
import threading


class aruco_tracker:
    
    jog_multiplier = 5
    deltaX = 0
    deltaY = 0
    jogX=0
    jogY=0
    staticTracking = True

    def __init__(self, controller):
         tracking = False
         self.controller = controller
         self.render_window = False

    def initialise_video(self):
        # initialize the video stream and allow the camera sensor to warm up
        print("[INFO] starting video stream...")
        self.vs = VideoStream(src=2,resolution=(1920,1080)).start()
        #vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)
        self.arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_100)
        
    def render_tracker(self, status):
        self.render_window = status
        
    def set_static_tracking(self, static_track):
        self.staticTracking=static_track

    def stop_tracking(self):
        self.tracking=False

    def start_tracking(self, trackedId):
        self.tracking=True
        self.track_target_id = trackedId
        self.thread = threading.Thread( 
            target=self.track, args=(trackedId,))
        #self.thread.daemon = True
        self.thread.start()

    def set_tracking_target(self,id):
        self.track_target_id=id

    def get_jogmultipliers(self):
        return self.jogX,self.jogY

    def track(self, trackedId):
        
        lastX=0
        lastY=0
        seen_waypoint_marker=False
        marker4=False
        firstTrack=True
        initialPositionX=0
        initialPositionY=0
        while self.tracking:
            if (trackedId != self.track_target_id):
                firstTrack=True
                trackedId=self.track_target_id
            xjog=0
            yjog=0
            # grab the frame from the threaded video stream and resize it to
            # have a maximum width of 800 pixels
            frame = self.vs.read()
            image = imutils.rotate(frame,180)
            #image = imutils.resize(image, width=800)
            # find the barcodes in the frame and decode each of the barcodes
            arucoParams = cv2.aruco.DetectorParameters_create()
            (corners, ids, rejected) = cv2.aruco.detectMarkers(image, self.arucoDict,parameters=arucoParams)
            # verify *at least* one ArUco marker was detected
            if len(corners) > 0:
                # flatten the ArUco IDs list
                ids = ids.flatten()
                # loop over the detected ArUCo corners
                maker4=False;
                for (markerCorner, markerID) in zip(corners, ids):
                    if (markerID == 4 & (seen_waypoint_marker ==False)):
                        #set waypoint
                        self.parent.add_waypoint()
                        #set toggle so we don't add again until we've had at least one frame without this marker
                        seen_waypoint_marker=True
                        marker4=True

                    if markerID == trackedId:
                        self.tracking_tag=True
                        trackedcorners = markerCorner.reshape((4, 2))
                        (tLeft, tRight, bRight, bLeft) = trackedcorners
                        trackedX = int((tLeft[0] + bRight[0]) / 2.0)
                        trackedY = int((tLeft[1] + bRight[1]) / 2.0)
                        if (trackedId == 1):
                            #tracker 1 always moves to position where it was to start with
                            
                            self.deltaX = (initialPositionX - trackedX)
                            self.deltaY = (initialPositionY - trackedY)
                        if (trackedId == 2):
                            height, width = image.shape[:2]
                            
                            #tracker 2 always centres
                            self.deltaX = ((width/2) - trackedX)
                            self.deltaY = ((height/2) - trackedY)
                        if (trackedId == 3):
                            height, width = image.shape[:2]
                            
                            #tracker 3 always centres horzontally and puts glyph at lower third
                            self.deltaX = ((width/2) - trackedX)
                            self.deltaY = ((height/3) - trackedY)
                        if (firstTrack == True):
                            #first instruction is always delta from a 0 which is a huge move
                            firstTrack = False
                            height, width = image.shape[:2]
                            print ("frame size x{} y{}".format(width,height))
                            
                            initialPositionX=trackedX
                            initialPositionY=trackedY
                            inittopRight = (int(tRight[0]), int(tRight[1]))
                            initbottomRight = (int(bRight[0]), int(bRight[1]))
                            initbottomLeft = (int(bLeft[0]), int(bLeft[1]))
                            inittopLeft = (int(tLeft[0]), int(tLeft[1]))
                        
                            print ("storing initial glyph discovery position x{} y{}".format(initialPositionX,initialPositionY))
                        else:
                            #print ("calculating jogging instruction to move glyph back to starting location {} {} by delta{} {}".format(initialPositionX, initialPositionY, self.deltaX, self.deltaY))
                            height, width = image.shape[:2]
                            
                            if (abs(self.deltaX) > 20):
                                xjog = -1*(self.deltaX/width)*self.jog_multiplier
                            else:
                                xjog=0
                            if (abs(self.deltaY) > 20):                            
                                yjog = -1*(self.deltaY / height)*self.jog_multiplier
                            else:
                                yjog=0
                            #print ("xjog {} yjog {}".format(xjog,yjog))

                            if ((self.staticTracking == True) & ((xjog !=0) | (yjog!=0))):
                                #move the opposite direction to the delta
                                self.controller.tracking_jog(xjog,yjog)
                                #give the move a chance to be made
                                self.jogX=0
                                self.jogY=0
                            else:
                                self.jogX = xjog
                                self.jogY = yjog
                            
                        lastX=trackedX
                        lastY=trackedY
                        #print ("tracking tag at x{}y{}".format(trackedX, trackedY))
                    if (self.render_window ==True):
                        # convert each of the (x, y)-coordinate pairs to integers
                        if (trackedcorners is not None):
                            (topLeft, topRight, bottomRight, bottomLeft) = trackedcorners
                
                            topRight = (int(topRight[0]), int(topRight[1]))
                            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
                            topLeft = (int(topLeft[0]), int(topLeft[1]))
                            # draw the bounding box of the ArUCo detection
                            cv2.line(image, topLeft, topRight, (0, 255, 0), 2)
                            cv2.line(image, topRight, bottomRight, (0, 255, 0), 2)
                            cv2.line(image, bottomRight, bottomLeft, (0, 255, 0), 2)
                            cv2.line(image, bottomLeft, topLeft, (0, 255, 0), 2)
                            # compute and draw the center (x, y)-coordinates of the ArUco
                        #draw inital location box
                        cv2.line(image, inittopLeft, inittopRight, (0, 0, 255), 2)
                        cv2.line(image, inittopRight, initbottomRight, (0, 0, 255), 2)
                        cv2.line(image, initbottomRight, initbottomLeft, (0, 0, 255), 2)
                        cv2.line(image, initbottomLeft, inittopLeft, (0, 0, 255), 2)
                        
                        # marker
                        cX = int((topLeft[0] + bottomRight[0]) / 2.0)
                        cY = int((topLeft[1] + bottomRight[1]) / 2.0)
                        cv2.circle(image, (cX, cY), 4, (0, 0, 255), -1)
                        # draw the ArUco marker ID on the image
                        cv2.putText(image, str(markerID),
                            (topLeft[0], topLeft[1] - 15), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 2)
                        #print("[INFO] ArUco marker ID: {}".format(markerID))
                        # show the output image
                        cv2.imshow("Image", image)
                        key = cv2.waitKey(1) & 0xFF
                if (marker4==False):
                    #if we didn't see marker 4 this time reset the toggle
                    seen_waypoint_marker=False

            