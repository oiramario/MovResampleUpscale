import os
from datetime import datetime

import ffmpeg

import usmodule.media as media
import usmodule.keyframe as keyframe
import usmodule.grid as grid
import usmodule.split as split
import usmodule.resample as resample
import usmodule.resize as resize
import usmodule.ebsynth as ebsynth


class Scaler:
    def __init__(self):
        # media.check()
        pass


    def process_video(self, media_path, output_path):
        if not os.path.isfile(media_path) or not os.path.isdir(output_path):
            return

        # stream infomation
        media_probe = ffmpeg.probe(media_path)
        Scaler.interrupt_operation = False

        # work path
        name, _ = os.path.splitext(os.path.basename(media_path))
        output_media_name = f'{name}-{datetime.now().strftime("%H_%M_%S")}'
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

        # resample
        resample_path = os.path.join(work_path, '2-resample')
        if not os.path.exists(resample_path):
            os.makedirs(resample_path)
        resample.series(frames_path, resample_path, frame_rate, resampled_fps)

        # super resolution
        super_resolution_path = os.path.join(work_path, '3-super_resolution')
        if not os.path.exists(super_resolution_path):
            os.makedirs(super_resolution_path)
        resize.upscale(resample_path, super_resolution_path)

        # merge new media
        output_media_file = os.path.join(output_path, f'{output_media_name}.mp4')
        media.merge(media_probe, super_resolution_path, audio_path, resampled_fps, output_media_file)

        return output_media_file
