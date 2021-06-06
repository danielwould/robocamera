# import the necessary packages
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import cv2

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
#vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)
arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_100)
trackedId=1
tracking=False
lastX=0
lastY=0
while True:
    
    # grab the frame from the threaded video stream and resize it to
    # have a maximum width of 800 pixels
    image = vs.read()
    image = imutils.resize(image, width=800)
    # find the barcodes in the frame and decode each of the barcodes
    arucoParams = cv2.aruco.DetectorParameters_create()
    (corners, ids, rejected) = cv2.aruco.detectMarkers(image, arucoDict,parameters=arucoParams)
    # verify *at least* one ArUco marker was detected
    if len(corners) > 0:
        # flatten the ArUco IDs list
        ids = ids.flatten()
        # loop over the detected ArUCo corners
        for (markerCorner, markerID) in zip(corners, ids):
            if markerID == trackedId:
                tracking=True
                trackedcorners = markerCorner.reshape((4, 2))
                (tLeft, tRight, bRight, bLeft) = trackedcorners
                trackedX = int((tLeft[0] + bRight[0]) / 2.0)
                trackedY = int((tLeft[1] + bRight[1]) / 2.0)
                deltaX = lastX-trackedX
                deltaY = lastY-trackedY
                print ("tracking delta {} {}".format(deltaX,deltaY))
                lastPos=(int(lastX), int(lastY))
                newPos = (int(trackedX), int(trackedY))
                cv2.line(image, lastPos, newPos, (0, 255, 0), 2)
                lastX=trackedX
                lastY=trackedY
                


            # extract the marker corners (which are always returned in
            # top-left, top-right, bottom-right, and bottom-left order)
            corners = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = corners
            # convert each of the (x, y)-coordinate pairs to integers
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

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break