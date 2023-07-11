import os
from datetime import datetime

import ffmpeg
import webuiapi
from PIL import Image

import usmodule.grid as grid
import usmodule.keyframe as keyframe
import usmodule.split as split
import usmodule.media as media


class Scaler:
    interrupt_operation = False

    def __init__(self, low_vram):
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
                # alwayson_scripts={
                #     'Tiled Diffusion': {
                #         'args': [{
                #             'enabled': True, 
                #             'method': 'Mixture of Diffusers',
                #             'overwrite_size': False, 
                #             'keep_input_size': True, 
                #             'image_width': src_image.width, 
                #             'image_height': src_image.height,
                #             'tile_width': 96, 
                #             'tile_height': 96, 
                #             'overlap': 48, 
                #             'tile_batch_size': 2 if self.low_vram else 8,
                #             'upscaler_name': None, 
                #             'scale_factor': scale,
                #             'noise_inverse': False, 
                #             'noise_inverse_steps': 10, 
                #             'noise_inverse_retouch': 1, 
                #             'noise_inverse_renoise_strength': 1, 
                #             'noise_inverse_renoise_kernel': 64,
                #             'control_tensor_cpu': False, 
                #             'enable_bbox_control': False, 
                #             'draw_background': False, 
                #             'causal_layers': False, 
                #             'bbox_control_states': {},
                #         }]
                #     },
                #     'Tiled VAE': {
                #         'args': [{
                #             'enabled': True,
                #             'encoder_tile_size': 1024 if self.low_vram else 3072,
                #             'decoder_tile_size': 128 if self.low_vram else 256, 
                #             'vae_to_gpu': True, 
                #             'fast_decoder': True, 
                #             'fast_encoder': True, 
                #             'color_fix': False
                #         }]
                #     }
                # }
            )
            result.image.save(os.path.join(odir, name))


    def process_video(self, media_path, output_path, scale_factor=2.0, sampling_steps=20, grid_rows=2, grid_cols=2):
        if not os.path.isfile(media_path) or not os.path.isdir(output_path):
            return

        # stream infomation
        media_probe = ffmpeg.probe(media_path)
        Scaler.interrupt_operation = False

        # work path
        output_media_name = f'{scale_factor}x-{datetime.now().strftime("%H_%M_%S")}'
        work_path = os.path.join(output_path, output_media_name)

        # extract streams from media
        frames_path = os.path.join(work_path, 'frames')
        if not os.path.exists(frames_path):
            os.makedirs(frames_path)
        audio_path = work_path
        media.extract(media_probe, media_path, frames_path, audio_path)

        # detect key frames
        # keyframes_path = os.path.join(work_path, 'keyframes')
        # if not os.path.exists(keyframes_path):
        #     os.makedirs(keyframes_path)
        # keyframe.extract(frames_path, keyframes_path, 0.3)

        # grid images
        # grids_path = os.path.join(work_path, 'grids')
        # if not os.path.exists(grids_path):
        #     os.makedirs(grids_path)
        # grid.extract(frames_path, frame_width, frame_height, grids_path, grid_rows, grid_cols)
        
        # upscale
        scaled_path = os.path.join(work_path, 'scaled')
        if not os.path.exists(scaled_path):
            os.makedirs(scaled_path)
        self.process_folder(frames_path, scaled_path, scale_factor, sampling_steps)

        # split grids
        # scaled_keyframes_path = os.path.join(work_path, 'scaled_keyframes')
        # if not os.path.exists(scaled_keyframes_path):
        #     os.makedirs(scaled_keyframes_path)
        # split.extract(8, scaled_grids_path, frame_width*scale_factor, frame_height*scale_factor, grid_rows, grid_cols, scaled_keyframes_path)
        
        # rename scaled_keyframes
        # keyframes = sorted(os.listdir(keyframes_path), reverse=True)
        # scaled_keyframes = sorted(os.listdir(scaled_keyframes_path), reverse=True)
        # for i in range(len(scaled_keyframes)):
        #     name = keyframes[i]
        #     src = os.path.join(scaled_keyframes_path, scaled_keyframes[i])
        #     dst = os.path.join(scaled_keyframes_path, name)
        #     os.rename(src, dst)
            

        # merge new media
        output_media_file = os.path.join(output_path, f'{output_media_name}.mp4')
        media.merge(media_probe, scaled_path, audio_path, output_media_file)

        return output_media_file