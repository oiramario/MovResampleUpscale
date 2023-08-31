import os

from PIL import Image
from tqdm import tqdm


def calc_grid_size(x):
    root = int(x ** 0.5)  # Integer square root of x
    row = col = root

    # Adjust row and col iteratively
    while row * col < x:
        if row <= col:
            row += 1
        else:
            col += 1

    return row, col


def combine(keyframes_path, grids_path):
    keyframes = sorted(os.listdir(keyframes_path))
    keyframe_count = len(keyframes)
    frame = Image.open(os.path.join(keyframes_path, keyframes[0]))
    frame_width, frame_height = frame.size

    grid_rows, grid_cols = calc_grid_size(keyframe_count)
    grid_size = grid_rows * grid_cols
    grid_width = grid_cols * frame_width
    grid_height = grid_rows * frame_height
    grid_image = Image.new('RGB', (grid_width, grid_height))

    with tqdm(total=keyframe_count, unit='split') as pbar:
        for i, frame_file in enumerate(keyframes):
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
                # 保存合并后的图像
                output_filename = os.path.join(grids_path, f'{((i + 1) // (grid_size)):05d}.png')
                grid_image.save(output_filename)
                # grid_image = Image.new('RGB', (grid_width, grid_height))

            pbar.update(1)

    # 如果还有剩余的图像未存储
    quotient, remainder = divmod(keyframe_count, grid_size)
    if remainder != 0:
        # 保存剩余的合并图像
        output_filename = os.path.join(grids_path, f'{quotient + 1:05d}.png')
        grid_image.save(output_filename)
        pbar.update(1)
