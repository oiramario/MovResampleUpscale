import math
import os

from PIL import Image
from tqdm import tqdm


def extract(keyframes_path, frame_width, frame_height, grids_path, grid_rows=2, grid_cols=2):
    image_paths = sorted(os.listdir(keyframes_path))
    image_count = len(image_paths)
    grid_count = math.ceil(image_count / 4)
    grid_size = grid_rows * grid_cols
    quotient, remainder = divmod(image_count, grid_size)
    pbar = tqdm(total=grid_count, unit='frame')
    grid_width = grid_cols * frame_width
    grid_height = grid_rows * frame_height
    grid_image = Image.new('RGB', (grid_width, grid_height))
    for i, frame_file in enumerate(image_paths):
        frame = Image.open(os.path.join(keyframes_path, frame_file))

        # 计算当前帧的位置
        row = (i // grid_cols) % grid_rows
        col = i % grid_cols

        # 计算当前帧在大图中的坐标
        x = col * frame_width
        y = row * frame_height

        # 将当前帧复制到合并图像的对应位置
        grid_image.paste(frame, (x, y))

        if (i + 1) % (grid_size) == 0:
            pbar.update(1)
            # 保存合并后的图像
            output_filename = os.path.join(grids_path, f'{((i + 1) // (grid_size)):05d}.png')
            grid_image.save(output_filename)
            # grid_image = Image.new('RGB', (grid_width, grid_height))

    # 如果还有剩余的图像未存储
    if remainder != 0:
        pbar.update(1)
        # 保存剩余的合并图像
        output_filename = os.path.join(grids_path, f'grid{quotient + 1:05d}.png')
        grid_image.save(output_filename)
