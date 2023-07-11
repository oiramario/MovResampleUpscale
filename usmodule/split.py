import os

from PIL import Image
from tqdm import tqdm


def extract(frame_count, grid_path, frame_width, frame_height, grid_rows, grid_cols, split_path):
    grid_images = sorted(os.listdir(grid_path))
    frame_index = 0
    with tqdm(total=frame_count, unit='frame') as pbar:
        for grid_file in grid_images:
            grid_image = Image.open(os.path.join(grid_path, grid_file))
            for row in range(grid_rows):
                for col in range(grid_cols):
                    # Calculate the coordinates of the current frame in the grid image
                    x = col * frame_width
                    y = row * frame_height

                    # Extract the frame from the grid image
                    frame = grid_image.crop((x, y, x + frame_width, y + frame_height))

                    # Save the extracted frame
                    output_filename = os.path.join(split_path, f'{frame_index:05d}.png')
                    frame.save(output_filename)

                    frame_index += 1
                    pbar.update(1)
                    if frame_index == frame_count:
                        return True
