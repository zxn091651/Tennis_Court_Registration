import cv2 as cv
import numpy as np

# The basic points in four perspective (corresponding to four cameras)
# which are used to calculate homography matrix
video_keypoint = np.array([[[491, 153], [101, 242], [908, 263], [366, 446]],
                           [[1379, 193], [962, 116], [1093, 416], [529, 250]],
                           [[345, 413], [885, 237], [45, 182], [452, 106]],
                           [[518, 296], [1045, 425], [925, 149], [1316, 195]]])

# The basic points in the tennis template
# which are used to calculate homography matrix
tennis_keypoint = np.array([[11.885, 5.020], [11.885, 13.250], [24.685, 5.020], [24.685, 13.250]])


# Get homography matrix
def get_homo(flag):
    # Get basic points in one perspective
    img_src_coordinate = video_keypoint[flag]

    # Calculate homography matrix
    matrix, mask = cv.findHomography(img_src_coordinate, tennis_keypoint, 0)
    print(f'matrix: {matrix}')
    # perspective_img = cv.warpPerspective(img_src, matrix, (img_dest.shape[1], img_dest.shape[0]))

    return matrix


# Person registration and visualization
def registration(person_point, matrix, id):
    if len(person_point) == 0:
        return []

    # Transform data format (u, v)T
    person_point = np.transpose(person_point)

    # Add one more dimension for every person (u, v, 1)T
    person_point = np.vstack((person_point, np.ones(len(person_point[0]))))

    # Using homography for registration
    homo_point = matrix @ person_point

    # Normalization
    norm_homo_point = [homo_point[0] / homo_point[2], homo_point[1] / homo_point[2]]

    # Transform data format
    norm_homo_point = np.asarray(norm_homo_point).transpose()

    # Transform id format and add it to nor_homo_point
    norm_homo_point = np.hstack((norm_homo_point, id))
    # print(norm_homo_point) 


    return norm_homo_point
