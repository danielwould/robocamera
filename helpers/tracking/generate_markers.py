# import the necessary packages
import numpy as np
import argparse
import cv2
import sys
import time

# load the ArUCo dictionary
arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_100)
# allocate memory for the output ArUCo tag and then draw the ArUCo
# tag on the output image
print("[INFO] generating ArUCo tag types") 
for i in range(100):
    tag = np.zeros((300, 300, 1), dtype="uint8")

    cv2.aruco.drawMarker(arucoDict, i, 300, tag, 1)
    # write the generated ArUCo tag to disk and then display it to our
    # screen
    print ("write tag {} to disk".format(i))
    cv2.imwrite("DICT_5X5_100_id{}.png".format(i), tag)
    cv2.imshow("ArUCo Tag", tag)
    cv2.waitKey(1)
    