# this is pending...
# This will entry point for data collection for image response to lambdas at core for applying decided models.
# 1) Will utilise trafficLight.py usage for subscribe.
# 2) Will trigger greengrassPublish.py which in turn will 
#  a) trigger realsense camera capture, 
#  b) saving of image, 
#  c) encoding to base64, 
#  d) deciding chunks,
#  e) iterate and publish over realsense/send/image topic all chunks from last step
