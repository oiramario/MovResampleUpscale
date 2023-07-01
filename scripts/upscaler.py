import os
import os.path
import pathlib
import re
import subprocess
from datetime import datetime

import gradio as gr
import torch.cuda
import webuiapi
from modules import devices, script_callbacks, shared
from modules.ui import save_style_symbol
from modules.ui_common import folder_symbol
from PIL import Image

# directory of the outputs
sd_path = pathlib.Path().absolute()
output_path = os.path.join(sd_path, 'outputs', 'upscaler')
if not os.path.exists(output_path):
    os.makedirs(output_path)

interrupt_operation = False

class Upscaler:
    def __init__(self):
        mem_stats = Upscaler.get_memory_stats()
        self.vram = mem_stats['total'] / 1024

        # create API client
        self.api = webuiapi.WebUIApi()
        # change sd model, vae
        options = {}
        options['sd_model_checkpoint'] = 'v2-1_768-ema-pruned'
        options['sd_vae'] = 'vqgan_cfw_00011_vae_only.ckpt'
        self.api.set_options(options)


    def get_memory_stats():
        devices.torch_gc()
        torch.cuda.reset_peak_memory_stats()
        shared.mem_mon.monitor()
        return {k: -(v//-(1024*1024)) for k, v in shared.mem_mon.stop().items()}


    def process(self, src, scale, steps):
        large_vram = self.vram > 20
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
                True, 
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
                        'image_width': src_image.width, 
                        'image_height': src_image.height,
                        'tile_width': 96 if large_vram else 64, 
                        'tile_height': 96 if large_vram else 64, 
                        'overlap': 48 if large_vram else 32, 
                        'tile_batch_size': 8 if large_vram else 1,
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
                    }]
                },
                'Tiled VAE': {
                    'args': [{
                        'enabled': True,
                        'encoder_tile_size': 3072 if large_vram else 1024,
                        'decoder_tile_size': 256 if large_vram else 128, 
                        'vae_to_gpu': True, 
                        'fast_decoder': True, 
                        'fast_encoder': True, 
                        'color_fix': 'False'
                    }]
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
            if interrupt_operation:
                raise InterruptedError
            if filename.endswith('png'):
                ifp = os.path.join(idir, filename)
                if os.path.isfile(ifp):
                    result = self.process(ifp, scale, steps)
                    ofp = os.path.join(odir, filename)
                    result.save(ofp)


    def process_video(self, ifp, odir, scale, steps):
        if not os.path.isfile(ifp) or not os.path.isdir(odir):
            return

        # check ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError:
            print('ffmpeg is missing...')
            return

        # get fps
        result = subprocess.run(f'ffmpeg -i "{ifp}"', capture_output=True)
        output = result.stderr.decode()
        has_audio = 'Stream #0:1' in output and 'Audio' in output
        crf = 18

        # extract image and audio from video
        frames_path = os.path.join(odir, 'frames')
        audio = os.path.join(frames_path, 'audio.mp3')
        if not os.path.exists(frames_path):
            os.makedirs(frames_path)
        image = os.path.join(frames_path, '%5d.png')
        cmd = f'ffmpeg -y -i "{ifp}" -r 24 -f image2 "{image}"'
        if has_audio:
            cmd += ' -f mp3 "{audio}"'
        if 0 != os.system(cmd):
            return

        # grid images
        rows, cols = 2, 2
        grids_path = os.path.join(odir, 'grids')
        if not os.path.exists(grids_path):
            os.makedirs(grids_path)
        frame_files = sorted(os.listdir(frames_path))
        frame_path = os.path.join(frames_path, frame_files[0])
        frame = Image.open(frame_path)
        frame_width = frame.width
        frame_height = frame.height
        grid_width = cols * frame_width
        grid_height = rows * frame_height
        grid_image = Image.new('RGB', (grid_width, grid_height))
        for i, frame_file in enumerate(frame_files):
            frame_path = os.path.join(frames_path, frame_file)
            frame = Image.open(frame_path)

            # 计算当前帧的位置
            row = (i // cols) % rows
            col = i % cols

            # 计算当前帧在大图中的坐标
            x = col * frame_width
            y = row * frame_height

            # 将当前帧复制到合并图像的对应位置
            grid_image.paste(frame, (x, y))
            #plt.imshow(grid_image)

            if (i + 1) % (rows * cols) == 0:
                # 保存合并后的图像
                output_filename = os.path.join(grids_path, f'{((i + 1) // (rows * cols)):05d}.png')
                grid_image.save(output_filename)

        # video filename -> scale-time.mp4
        current = datetime.now().strftime("%H_%M_%S")
        current = f'{scale}x-{current}'
        target = os.path.join(odir, current)
        if not os.path.exists(target):
            os.makedirs(target)

        try:
            # set 0 to redesign ui
            if 1:
                # scale images
                self.process_folder(grids_path, target, scale, steps)
            else:
                target = grids_path

            # combine frames with audio to video
            image = os.path.join(target, '%5d.png')
            video = os.path.join(odir, f'{current}.mp4')
            cmd = f'ffmpeg -y -r 24 -i "{image}" -c:v libx264 -pix_fmt yuv420p -crf {crf} "{video}"'
            if has_audio:
                cmd += ' -i "{audio}"'
            if 0 != os.system(cmd):
                return
            return video
        except InterruptedError:
            pass


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


def generate(src_video, scale_factor, sampling_steps):
    if not src_video:
        return

    global interrupt_operation
    interrupt_operation = False
    work_dir = work_folder(src_video)
    scaler = Upscaler()
    return scaler.process_video(src_video, work_dir, scale_factor, sampling_steps)


def interrupt():
    global interrupt_operation
    interrupt_operation = True
    shared.state.interrupt()


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as upscaler_interface:
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    src_video = gr.Video(interactive=True, include_audio=True)
                with gr.Row():
                    scale_factor = gr.Slider(minimum=1, maximum=10, value=2.0, step=0.1, label='Scale factor:')
                    sampling_steps = gr.Slider(minimum=20, maximum=100, value=20, step=1, label='Sampling steps:')
                with gr.Row():
                    btn_generate = gr.Button('Generate', variant='primary')
                    btn_interrupt = gr.Button('Interrupt')
            with gr.Column():
                with gr.Row():
                    dst_video = gr.Video(interactive=False, include_audio=True)
                with gr.Row():
                    btn_open_folder = gr.Button(folder_symbol)
                    btn_save = gr.Button(save_style_symbol)
                with gr.Row():
                     download_file = gr.File(None, interactive=False, show_label=False, visible=False)

        btn_generate.click(
            fn=generate, 
            inputs=[src_video, scale_factor, sampling_steps], 
            outputs=dst_video, 
            show_progress=True)

        btn_interrupt.click(
            fn=interrupt,
            inputs=[],
            outputs=[],
        )

        btn_open_folder.click(
            fn=lambda x, y: os.startfile(work_folder(x)) if x and y else None,
            inputs=[src_video, dst_video])

        btn_save.click(
            fn=lambda x: gr.File.update(value=x, show_label=True, visible=True) if x else None,
            inputs=dst_video,
            outputs=download_file)

    return (upscaler_interface, "Upscaler", "upscaler_interface"),


script_callbacks.on_ui_tabs(on_ui_tabs)
