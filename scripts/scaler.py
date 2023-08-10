import os
from datetime import datetime

import ffmpeg

import usmodule.media as media
import usmodule.keyframe as keyframe
import usmodule.grid as grid
import usmodule.split as split
import usmodule.realesrgan as realesrgan
import usmodule.ebsynth as ebsynth


class Scaler:
    interrupt_operation = False

    def __init__(self, low_vram):
        # media.check()
        self.low_vram = low_vram


    def process_video(self, media_path, output_path, scale_factor):
        if not os.path.isfile(media_path) or not os.path.isdir(output_path):
            return

        # stream infomation
        media_probe = ffmpeg.probe(media_path)
        Scaler.interrupt_operation = False

        # work path
        output_media_name = f'{scale_factor}x-{datetime.now().strftime("%H_%M_%S")}'
        work_path = os.path.join(output_path, output_media_name)

        # frames
        frames_path = os.path.join(work_path, '1-frames')
        if not os.path.exists(frames_path):
            os.makedirs(frames_path)
        audio_path = work_path
        media.extract(media_probe, media_path, frames_path, audio_path, None)

        # scale frames
        # scale_frames_path = os.path.join(work_path, '2-scale_frames')
        # if not os.path.exists(scale_frames_path):
        #     os.makedirs(scale_frames_path)
        # media.extract(media_probe, media_path, scale_frames_path, None, scale_factor)

        # keyframes
        # keyframes_path = os.path.join(work_path, '3-keyframes')
        # if not os.path.exists(keyframes_path):
        #     os.makedirs(keyframes_path)
        # keyframe.analyze(frames_path, keyframes_path, key_min_gap, key_max_gap, key_th, True)

        # grid
        # grid_path = os.path.join(work_path, '4-grid')
        # if not os.path.exists(grid_path):
        #     os.makedirs(grid_path)
        # grid.combine(keyframes_path, grid_path)

        # scale grid
        scale_grid_path = os.path.join(work_path, '5-scale_grid')
        if not os.path.exists(scale_grid_path):
            os.makedirs(scale_grid_path)
        realesrgan.upscale(frames_path, scale_grid_path)

        # split scale keyframes
        # scale_keyframes_path = os.path.join(work_path, '6-scale_keyframes')
        # if not os.path.exists(scale_keyframes_path):
        #     os.makedirs(scale_keyframes_path)
        # split.extract(keyframes_path, scale_grid_path, scale_keyframes_path)

        # ebsynth frames
        # ebsynth_frames_path = os.path.join(work_path, '7-ebsynth_frames')
        # if not os.path.exists(ebsynth_frames_path):
        #     os.makedirs(ebsynth_frames_path)
        # ebsynth.run(scale_frames_path, scale_grid_path, ebsynth_frames_path)

        # merge new media
        output_media_file = os.path.join(output_path, f'{output_media_name}.mp4')
        media.merge(media_probe, scale_grid_path, audio_path, output_media_file)

        return output_media_file
