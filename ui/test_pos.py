import pylon_shm
# import camera_thread
import cv2


cam_=pylon_shm.PYLON_SHM('Center')
#thread_=camera_thread.GrabbingThread(cam_)

points=[[15.581, 10.5784, 1],
        [23.332, 11.822, 2],
        [3.000, 3.000, 3]]


cam_.set_2dpoints(points)

