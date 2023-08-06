import glob
import math
import os
import shutil

import cv2
import numpy as np

from tqdm import tqdm

#---------------------------------
# Copied from PySceneDetect
def mean_pixel_distance(left: np.ndarray, right: np.ndarray) -> float:
    """Return the mean average distance in pixel values between `left` and `right`.
    Both `left and `right` should be 2 dimensional 8-bit images of the same shape.
    """
    assert len(left.shape) == 2 and len(right.shape) == 2
    assert left.shape == right.shape
    num_pixels: float = float(left.shape[0] * left.shape[1])
    return (np.sum(np.abs(left.astype(np.int32) - right.astype(np.int32))) / num_pixels)


def estimated_kernel_size(frame_width: int, frame_height: int) -> int:
    """Estimate kernel size based on video resolution."""
    size: int = 4 + round(math.sqrt(frame_width * frame_height) / 192)
    if size % 2 == 0:
        size += 1
    return size

_kernel = None

def _detect_edges(lum: np.ndarray) -> np.ndarray:
    global _kernel
    """Detect edges using the luma channel of a frame.
    Arguments:
        lum: 2D 8-bit image representing the luma channel of a frame.
    Returns:
        2D 8-bit image of the same size as the input, where pixels with values of 255
        represent edges, and all other pixels are 0.
    """
    # Initialize kernel.
    if _kernel is None:
        kernel_size = estimated_kernel_size(lum.shape[1], lum.shape[0])
        _kernel = np.ones((kernel_size, kernel_size), np.uint8)

    # Estimate levels for thresholding.
    sigma: float = 1.0 / 3.0
    median = np.median(lum)
    low = int(max(0, (1.0 - sigma) * median))
    high = int(min(255, (1.0 + sigma) * median))

    # Calculate edges using Canny algorithm, and reduce noise by dilating the edges.
    # This increases edge overlap leading to improved robustness against noise and slow
    # camera movement. Note that very large kernel sizes can negatively affect accuracy.
    edges = cv2.Canny(lum, low, high)
    return cv2.dilate(edges, _kernel)

#---------------------------------

def detect_edges(img_path):
    im = cv2.imread(img_path)
    hue, sat, lum = cv2.split(cv2.cvtColor( im , cv2.COLOR_BGR2HSV))
    return _detect_edges(lum)

def analyze(png_dir, key_dir, min_gap, max_gap, th, add_last_frame):
    keys = []

    frames = sorted(glob.glob( os.path.join(png_dir, "[0-9]*.png") ))

    key_frame = frames[0]
    keys.append( int(os.path.splitext(os.path.basename(key_frame))[0]) )
    key_edges = detect_edges( key_frame )
    gap = 0

    with tqdm(total=len(frames), unit='keyframe') as pbar:
        for frame in frames:
            pbar.update(1)
            gap += 1
            if gap < min_gap:
                continue
            
            edges = detect_edges( frame )
            
            delta = mean_pixel_distance( edges, key_edges )
            
            _th = th * (max_gap - gap)/max_gap
            
            if _th < delta:
                basename_without_ext = os.path.splitext(os.path.basename(frame))[0]
                keys.append( int(basename_without_ext) )
                key_frame = frame
                key_edges = edges
                gap = 0

    if add_last_frame:
        basename_without_ext = os.path.splitext(os.path.basename(frames[-1]))[0]
        last_frame = int(basename_without_ext)
        if not last_frame in keys:
            keys.append( last_frame )

    for k in keys:
        filename = str(k).zfill(5) + ".png"
        shutil.copy( os.path.join( png_dir , filename) , os.path.join(key_dir, filename) )

def remove_pngs_in_dir(path):
    if not os.path.isdir(path):
        return

    pngs = glob.glob( os.path.join(path, "*.png") )
    for png in pngs:
        os.remove(png)
