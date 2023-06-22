import os.path
import pathlib
import re
import subprocess
from datetime import datetime

import gradio as gr
import modules
from modules.ui_common import folder_symbol, plaintext_to_html

# directory of the outputs
sd_path = pathlib.Path().absolute()
output_path = os.path.join(sd_path, 'outputs', 'upscaler')
if not os.path.exists(output_path):
    os.makedirs(output_path)

# directory of the extension
ext_path = modules.scripts.basedir()

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


def upscale_gen(src_video, scale_factor):
    if not src_video:
        print('select a video first...')
        return

    # check ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        print('ffmpeg is missing...')
        return

    # get bit_rate, fps
    result = subprocess.run(f'ffmpeg -i "{src_video}"', capture_output=True)
    output = result.stderr.decode()
    match = re.search(r"(\d+) kb/s, (\d+) fps", output)
    if not match:
        print('ffmpeg cannot get video infomation...')
        return
    bit_rate = int(match.group(1))
    fps = int(match.group(2))

    # create directories
    work_dir = work_folder(src_video)
    frames_path = os.path.join(work_dir, 'frames')
    if not os.path.exists(frames_path):
        os.makedirs(frames_path)

    # extract frames from video
    frames = os.path.join(frames_path, '%5d.png')
    if 0 != os.system(f'ffmpeg -r {fps} -i "{src_video}" "{frames}"'):
        return

    # merge frames to video
    current = datetime.now().strftime("%H_%M_%S")
    dst_path = os.path.join(work_dir, f'{scale_factor}x-{current}.mp4')
    # -b:v {bit_rate}k
    if 0 != os.system(f'ffmpeg -y -r {fps} -i "{frames}" -c:v libx264 -pix_fmt yuv420p "{dst_path}"'):
        return

    return dst_path


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
                    scale_factor = gr.Slider(minimum=1, maximum=16, step=0.1, value=2, label='Scale Factor')
                    btn_generate = gr.Button('Generate', variant='primary')

            with gr.Column():
                dst_video = gr.Video(interactive=False, label='Upscaled')
                with gr.Row():
                    btn_open_folder = gr.Button(folder_symbol)
                    btn_save = gr.Button('Save')
                with gr.Row():
                     download_file = gr.File(None, interactive=False, show_label=False, visible=False)

        btn_generate.click(
            fn=upscale_gen, 
            inputs=[src_video, scale_factor], 
            outputs=dst_video, 
            show_progress=True)

        btn_open_folder.click(
            fn=open_folder,
            inputs=[src_video, dst_video])

        btn_save.click(
            fn=save_as,
            inputs=dst_video,
            outputs=download_file)

    return (upscaler_interface, "Upscaler", "upscaler_interface"),


modules.script_callbacks.on_ui_tabs(on_ui_tabs)
