import os
from datetime import datetime

import ffmpeg

import modules.media as media
import modules.resize as resize
#import usmodule.keyframe as keyframe
#import usmodule.grid as grid
#import usmodule.split as split
import modules.series as series

#import usmodule.ebsynth as ebsynth


def process_video(media_path, output_path, restoration, animvideo):
    if not os.path.isfile(media_path) or not os.path.isdir(output_path):
        return

    # stream infomation
    media_probe = ffmpeg.probe(media_path)

    # work path
    output_media_name = f'{datetime.now().strftime("%H_%M_%S")}'
    work_path = os.path.join(output_path, output_media_name)
    audio_path = work_path

    # frame_rate
    video_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'video'), None)
    frame_rate = int(eval(video_stream['r_frame_rate']))
    resampled_fps = frame_rate * 2

    # frames
    frames_path = os.path.join(work_path, '1-frames')
    if not os.path.exists(frames_path):
        os.makedirs(frames_path)
    media.extract(media_probe, media_path, frames_path, frame_rate, audio_path)

    # restoration [option]
    if restoration:
        restoration_path = os.path.join(work_path, '2-restoration')
        if not os.path.exists(restoration_path):
            os.makedirs(restoration_path)
        series.restoration(frames_path, restoration_path)
    else:
        restoration_path = frames_path

    # resample
    resample_path = os.path.join(work_path, '3-resample')
    if not os.path.exists(resample_path):
        os.makedirs(resample_path)
    series.resample(restoration_path, resample_path, frame_rate, resampled_fps)

    # super resolution
    super_resolution_path = os.path.join(work_path, '4-super_resolution')
    if not os.path.exists(super_resolution_path):
        os.makedirs(super_resolution_path)
    resize.upscale(resample_path, super_resolution_path, animvideo)

    # merge new media
    output_media_file = os.path.join(output_path, f'{output_media_name}.mp4')
    media.merge(media_probe, super_resolution_path, audio_path, resampled_fps, output_media_file)

    return output_media_file
