from absl import app, flags
from absl.flags import FLAGS
# from YOLOv9_DeepSORT.yolov9.object_tracking_stream import person_track_stream
from YOLOv9_DeepSORT.yolov9.object_tracking import person_track

# Define command line flags
flags.DEFINE_string('video', './data/video_0.mp4', 'Path to input video or video stream (0)')
flags.DEFINE_float('conf', 0.50, 'confidence threshold')
flags.DEFINE_integer('blur_id', None, 'class ID to apply Gaussian Blur')
flags.DEFINE_integer('class_id', 0, 'class ID to track')
flags.DEFINE_integer('cam_id', 0, 'camera perspective ID to track')


def main(_argv):
    if FLAGS.video.isdigit():
        print("#### Stream Mode ####")
        # person_track_stream(FLAGS)
    else:
        print("#### Video Mode ####")
        person_track(FLAGS)


if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
