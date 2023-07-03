import datetime
import os

import ffmpeg

import module.grid as grid
import module.keyframe as keyframe
import module.media as media


def process_video(media_path, output_path, scale_factor=2.0, steps=20, grid_rows=2, grid_cols=2):
    if not os.path.isfile(media_path) or not os.path.isdir(output_path):
        return

    # stream infomation
    media_probe = ffmpeg.probe(media_path, hide_banner=None)
    video_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'video'), None)
    if not video_stream:
        return

    # video properties
    frame_width = video_stream['width']
    frame_height = video_stream['height']
    frame_rate = eval(video_stream['avg_frame_rate'])

    # work path
    output_media_name = f'{scale_factor}x-{datetime.datetime.now().strftime("%H_%M_%S")}'
    work_path = os.path.join(output_path, output_media_name)

    # extract streams from media
    frames_path = os.path.join(work_path, 'frames')
    if not os.path.exists(frames_path):
        os.makedirs(frames_path)
    audio_path = work_path
    media.extract(media_probe, media_path, frames_path, audio_path)

    # detect key frames
    keyframes_path = os.path.join(work_path, 'keyframes')
    if not os.path.exists(keyframes_path):
        os.makedirs(keyframes_path)
    keyframe.extract(frames_path, keyframes_path, 0.3)

    # grid images
    grids_path = os.path.join(work_path, 'grids')
    if not os.path.exists(grids_path):
        os.makedirs(grids_path)
    grid.extract(keyframes_path, frame_width, frame_height, grids_path, grid_rows, grid_cols)

    # media name -> scale_factor-time.mp4
    output_media_file = os.path.join(output_path, f'{output_media_name}.mp4')
    media.merge(media_probe, grids_path, frame_rate, audio_path, output_media_file)

process_video(r'F:\ai\test\1.mp4', r'F:\ai\test\output', 2.0, 20)
