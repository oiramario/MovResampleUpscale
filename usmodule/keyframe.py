import os

import cv2
import numpy as np
import peakutils
from PIL import Image
from tqdm import tqdm


def scale(img, xScale, yScale):
    res = cv2.resize(img, None, fx=xScale, fy=yScale, interpolation=cv2.INTER_AREA)
    return res


def convert_frame_to_grayscale(frame):
    numpy_array = np.array(frame)
    gray = cv2.cvtColor(numpy_array, cv2.COLOR_BGR2GRAY)
    gray = scale(gray, 1, 1)
    gray = cv2.GaussianBlur(gray, (9, 9), 0.0)
    return gray


def extract(frames_path, keyframes_path, thres):
    image_paths = sorted(os.listdir(frames_path))

    lstdiffMag = []
    full_color = []
    lastFrame = None
    
    with tqdm(total=len(image_paths), desc="Processing frames") as pbar:
        for frame_number, frame_file in enumerate(image_paths):
            frame = Image.open(os.path.join(frames_path, frame_file))
            blur_gray = convert_frame_to_grayscale(frame)

            full_color.append(frame)
            if frame_number == 0:
                lastFrame = blur_gray

            diff = cv2.subtract(blur_gray, lastFrame)
            diffMag = cv2.countNonZero(diff)
            lstdiffMag.append(diffMag)
            lastFrame = blur_gray
        pbar.update(1)

    y = np.array(lstdiffMag)
    base = peakutils.baseline(y, 2)
    indices = peakutils.indexes(y-base, thres, min_dist=1)

    for x in indices:
        full_color[x].save(os.path.join(keyframes_path , f'{x:05d}.png'))
    full_color[-1].save(os.path.join(keyframes_path , f'{len(full_color):05d}.png'))
