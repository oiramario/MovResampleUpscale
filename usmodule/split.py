import os

from PIL import Image
from tqdm import tqdm


def calc_grid_size(x):
    root = int(x ** 0.5)  # Integer square root of x
    row = col = root

    if row * col < x:
        row += 1
    if row * col < x:
        col += 1

    return row, col


def extract(keyframes_path, grids_path, splits_path):
    keyframes = sorted(os.listdir(keyframes_path))
    keyframe_count = len(keyframes)

    grid_rows, grid_cols = calc_grid_size(keyframe_count)
    grid_images = sorted(os.listdir(grids_path))
    grid = Image.open(os.path.join(grids_path, grid_images[0]))
    grid_width, grid_height = grid.size
    frame_width = int(grid_width / grid_cols)
    frame_height = int(grid_height / grid_rows)

    frame_index = 0
    with tqdm(total=keyframe_count, unit='split') as pbar:
        for grid_file in grid_images:
            grid_image = Image.open(os.path.join(grids_path, grid_file))
            for row in range(grid_rows):
                for col in range(grid_cols):
                    # Calculate the coordinates of the current frame in the grid image
                    x = col * frame_width
                    y = row * frame_height

                    # Extract the frame from the grid image
                    frame = grid_image.crop((x, y, x + frame_width, y + frame_height))

                    # Save the extracted frame
                    name = keyframes[frame_index]
                    output_filename = os.path.join(splits_path, name)
                    frame.save(output_filename)

                    frame_index += 1
                    pbar.update(1)
                    if frame_index == keyframe_count:
                        return True
