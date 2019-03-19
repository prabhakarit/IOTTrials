## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

###############################################
##      Open CV and Numpy integration        ##
###############################################

import pyrealsense2 as rs
import numpy as np
import cv2
from time import sleep

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

# Wait for a coherent pair of frames: depth and color
frames = pipeline.wait_for_frames()
color_frame = frames.get_color_frame()
if not color_frame:
   pipeline.stop()
   exit()

# Sleep for 5 second
sleep(5)

# Convert images to numpy arrays
color_image = np.asanyarray(color_frame.get_data())

# saving images
cv2.imwrite('color_image_simple.png', color_image)

# Stop streaming
pipeline.stop()
