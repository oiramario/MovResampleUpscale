import os
import os.path
import pathlib
import re
import subprocess
from datetime import datetime

import gradio as gr
import modules
import webuiapi
from modules.ui_common import folder_symbol
from PIL import Image

# directory of the outputs
sd_path = pathlib.Path().absolute()
output_path = os.path.join(sd_path, 'outputs', 'upscaler')
if not os.path.exists(output_path):
    os.makedirs(output_path)

# directory of the extension
ext_path = modules.scripts.basedir()


class Upscaler:
    def __init__(self):
        # create API client
        self.api = webuiapi.WebUIApi()

        # change sd model, vae
        options = {}
        options['sd_model_checkpoint'] = 'v2-1_768-ema-pruned'
        options['sd_vae'] = 'vqgan_cfw_00011_vae_only.ckpt'
        self.api.set_options(options)


    def interrupt():
        webuiapi.WebUIApi().interrupt()


    def process(self, src, scale, steps):
        src_image = Image.open(src)
        result = self.api.img2img(
            images=[src_image], 
            cfg_scale=2, 
            sampler_name='Euler a', 
            steps=steps,
            script_name='StableSR',
            script_args=[
                'webui_768v_139.ckpt', 
                scale,
                'Wavelet',
                False,
                True
            ],
            alwayson_scripts={
                'Tiled Diffusion': {
                    'args': [
                        {
                            'enabled': True, 
                            'method': 'Mixture of Diffusers',
                            'overwrite_size': False, 
                            'keep_input_size': True, 
                            'image_width': src_image.width, 
                            'image_height': src_image.height,
                            'tile_width': 96, 
                            'tile_height': 96, 
                            'overlap': 48, 
                            'tile_batch_size': 8,
                            'upscaler_name': None, 
                            'scale_factor': scale,
                            'noise_inverse': False, 
                            'noise_inverse_steps': 10, 
                            'noise_inverse_retouch': 1.0, 
                            'noise_inverse_renoise_strength': 1.0, 
                            'noise_inverse_renoise_kernel': 64,
                            'control_tensor_cpu': False, 
                            'enable_bbox_control': False, 
                            'draw_background': False, 
                            'causal_layers': False, 
                            'bbox_control_states': {},
                        }
                    ]
                },
                'Tiled VAE': {
                    'args': [
                        {
                            'enabled': True,
                            'encoder_tile_size': 3072,
                            'decoder_tile_size': 256, 
                            'vae_to_gpu': True, 
                            'fast_decoder': True, 
                            'fast_encoder': True, 
                            'color_fix': 'False'
                        }
                    ]
                }
            })
        return result.image


    def process_file(self, ifp, odir, scale, steps):
        if not os.path.isfile(ifp) or not os.path.isdir(odir):
            return
        result = self.process(ifp, scale, steps)
        ofp = os.path.join(odir, os.path.basename(ifp))
        result.save(ofp)


    def process_folder(self, idir, odir, scale, steps):
        if not os.path.isdir(idir) or not os.path.isdir(odir):
            return
        for filename in os.listdir(idir):
            if filename.endswith('png'):
                ifp = os.path.join(idir, filename)
                if os.path.isfile(ifp):
                    result = self.process(ifp, scale, steps)
                    ofp = os.path.join(odir, filename)
                    result.save(ofp)


    def process_video(self, ifp, odir, scale, steps, const_rate_factor):
        if not os.path.isfile(ifp) or not os.path.isdir(odir):
            return

        # check ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError:
            print('ffmpeg is missing...')
            return

        # get bit_rate, fps
        result = subprocess.run(f'ffmpeg -i "{ifp}"', capture_output=True)
        output = result.stderr.decode()
        match = re.search(r"(\d+) fps", output)
        if not match:
            print('ffmpeg cannot get video infomation...')
            return
        fps = int(match.group(1))

        # create directories
        frames_path = os.path.join(odir, 'frames')
        if not os.path.exists(frames_path):
            os.makedirs(frames_path)
            # extract images from video
            src_images = os.path.join(frames_path, '%5d.png')
            if 0 != os.system(f'ffmpeg -r {fps} -i "{ifp}" "{src_images}"'):
                return

        # scale images
        current = datetime.now().strftime("%H_%M_%S")
        if const_rate_factor > 0:
            factors = [18, 21, 24, 27]
            crf = factors[const_rate_factor - 1]
            output = f'{scale}x_{crf}-{current}'
        else:
            output = f'{scale}x_auto-{current}'
        output_path = os.path.join(odir, output)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        self.process_folder(frames_path, output_path, scale, steps)

        # video filename -> scale_rate_time.mp4
        upscaled_images = os.path.join(output_path, '%5d.png')
        args = f'-r {fps} -i "{upscaled_images}" -c:v libx264 -pix_fmt yuv420p'
        # bitrate
        if const_rate_factor > 0:
            args += f' -crf {crf}'
        # merge frames to video
        dst_path = os.path.join(odir, f'{output}.mp4')
        if 0 != os.system(f'ffmpeg -y {args} "{dst_path}"'):
            return
        
        return dst_path


def work_folder(src_video):
    if not src_video:
        return

    # create directories
    today = datetime.now().strftime("%Y-%m-%d")
    today_path = os.path.join(output_path, today)
    if not os.path.exists(today_path):
        os.makedirs(today_path)

    name, ext = os.path.splitext(os.path.basename(src_video))

    work_dir = os.path.join(today_path, name)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    return work_dir


def generate(src_video, const_rate_factor, scale_factor, sampling_steps):
    if not src_video:
        return

    # create directories
    work_dir = work_folder(src_video)

    scaler = Upscaler()
    dst_path = scaler.process_video(src_video, work_dir, scale_factor, sampling_steps, const_rate_factor)

    return dst_path


def interrupt():
    Upscaler.interrupt()


def open_folder(src_video, dst_video):
    if not src_video or not dst_video:
        return

    work_dir = work_folder(src_video)
    os.startfile(work_dir)


def save_as(dst_video):
    if not dst_video:
        return

    return gr.File.update(value=dst_video, show_label=True, visible=True)


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as upscaler_interface:
        with gr.Row().style(equal_height=False):
            with gr.Column():
                src_video = gr.Video(interactive=True, label='Original')
                with gr.Row():
                    const_rate_factor = gr.Radio(["Auto", "Ultra(18)", "High(21)", "Good(24)", "Medium(27)"], value="Auto", type="index", label = "Constant Rate Factor:")
                with gr.Row():
                    scale_factor = gr.Slider(minimum=1, maximum=10, value=2.0, step=0.1, label='Scale factor:')
                    sampling_steps = gr.Slider(minimum=1, maximum=100, value=20, step=1, label='Sampling steps:')
                with gr.Row():
                    btn_generate = gr.Button('Generate', variant='primary')
                    btn_interrupt = gr.Button('Interrupt')

            with gr.Column():
                dst_video = gr.Video(interactive=False, label='Upscaled')
                with gr.Row():
                    btn_open_folder = gr.Button(folder_symbol)
                    btn_save = gr.Button('Save')
                with gr.Row():
                     download_file = gr.File(None, interactive=False, show_label=False, visible=False)

        btn_generate.click(
            fn=generate, 
            inputs=[src_video, const_rate_factor, scale_factor, sampling_steps], 
            outputs=dst_video, 
            show_progress=True)
        
        btn_interrupt.click(
            fn=interrupt,
        )

        btn_open_folder.click(
            fn=open_folder,
            inputs=[src_video, dst_video])

        btn_save.click(
            fn=save_as,
            inputs=dst_video,
            outputs=download_file)

    return (upscaler_interface, "Upscaler", "upscaler_interface"),


modules.script_callbacks.on_ui_tabs(on_ui_tabs)
