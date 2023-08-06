import os
from datetime import datetime

import ffmpeg
import webuiapi
from PIL import Image

import usmodule.media as media
import usmodule.keyframe as keyframe
import usmodule.grid as grid
import usmodule.split as split
import usmodule.ebsynth as ebsynth


class Scaler:
    interrupt_operation = False

    def __init__(self, low_vram):
        # media.check()
        self.low_vram = low_vram
        self.api = webuiapi.WebUIApi()
        options = {}
        options['sd_model_checkpoint'] = 'v2-1_768-ema-pruned'
        options['sd_vae'] = 'vqgan_cfw_00011_vae_only.ckpt'
        self.api.set_options(options)


    def process_folder(self, idir, odir, scale, steps):
        frames = sorted(os.listdir(idir))
        for name in frames:
            result = self.api.img2img(
                images=[Image.open(os.path.join(idir, name))], 
                cfg_scale=7,
                seed=9981,
                denoising_strength=1,
                sampler_name='Euler a', 
                prompt='(masterpiece:2), (best quality:2), (realistic:2),(very clear:2)',
                negative_prompt='3d, cartoon, anime, sketches, (worst quality:2), (low quality:2)',
                steps=steps,
                script_name='StableSR',
                script_args=[
                    'webui_768v_139.ckpt', 
                    scale, 
                    False, 
                    'Wavelet', 
                    False
                ],
                alwayson_scripts={
                    'Tiled Diffusion': {
                        'args': [{
                            'enabled': True, 
                            'method': 'Mixture of Diffusers',
                            'overwrite_size': False, 
                            'keep_input_size': True, 
                            'image_width': 512, 
                            'image_height': 512,
                            'tile_width': 96, 
                            'tile_height': 96, 
                            'overlap': 48, 
                            'tile_batch_size': 2 if self.low_vram else 8,
                            'upscaler_name': None, 
                            'scale_factor': scale,
                            'noise_inverse': False, 
                            'noise_inverse_steps': 10, 
                            'noise_inverse_retouch': 1, 
                            'noise_inverse_renoise_strength': 1, 
                            'noise_inverse_renoise_kernel': 64,
                            'control_tensor_cpu': False, 
                            'enable_bbox_control': False, 
                            'draw_background': False, 
                            'causal_layers': False, 
                            'bbox_control_states': {},
                        }]
                    },
                    'Tiled VAE': {
                        'args': [{
                            'enabled': True,
                            'encoder_tile_size': 1024 if self.low_vram else 3072,
                            'decoder_tile_size': 128 if self.low_vram else 256, 
                            'vae_to_gpu': True, 
                            'fast_decoder': True, 
                            'fast_encoder': True, 
                            'color_fix': False
                        }]
                    }
                }
            )
            result.image.save(os.path.join(odir, name))


    def process_video(self, media_path, output_path, scale_factor, sampling_steps, key_min_gap, key_max_gap, key_th):
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
        scale_frames_path = os.path.join(work_path, '2-scale_frames')
        if not os.path.exists(scale_frames_path):
            os.makedirs(scale_frames_path)
        media.extract(media_probe, media_path, scale_frames_path, None, scale_factor)

        # keyframes
        keyframes_path = os.path.join(work_path, '3-keyframes')
        if not os.path.exists(keyframes_path):
            os.makedirs(keyframes_path)
        keyframe.analyze(frames_path, keyframes_path, key_min_gap, key_max_gap, key_th, True)

        # grid
        grid_path = os.path.join(work_path, '4-grid')
        if not os.path.exists(grid_path):
            os.makedirs(grid_path)
        grid.combine(keyframes_path, grid_path)

        # scale grid
        scale_grid_path = os.path.join(work_path, '5-scale_grid')
        if not os.path.exists(scale_grid_path):
            os.makedirs(scale_grid_path)
        self.process_folder(grid_path, scale_grid_path, scale_factor, sampling_steps)

        # split scale keyframes
        scale_keyframes_path = os.path.join(work_path, '6-scale_keyframes')
        if not os.path.exists(scale_keyframes_path):
            os.makedirs(scale_keyframes_path)
        split.extract(keyframes_path, scale_grid_path, scale_keyframes_path)

        # ebsynth frames
        ebsynth_frames_path = os.path.join(work_path, '7-ebsynth_frames')
        if not os.path.exists(ebsynth_frames_path):
            os.makedirs(ebsynth_frames_path)
        ebsynth.run(scale_frames_path, scale_keyframes_path, ebsynth_frames_path)

        # merge new media
        output_media_file = os.path.join(output_path, f'{output_media_name}.mp4')
        media.merge(media_probe, ebsynth_frames_path, audio_path, output_media_file)

        return output_media_file
