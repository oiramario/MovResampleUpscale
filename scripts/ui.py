import os
import os.path
import pathlib
from datetime import datetime

import gradio as gr
import torch.cuda
from modules import script_callbacks, devices, shared
from modules.ui import save_style_symbol
from modules.ui_common import folder_symbol

from scripts.scaler import Scaler

# directory of the outputs
sd_path = pathlib.Path().absolute()
output_path = os.path.join(sd_path, 'outputs', 'upscaler')
if not os.path.exists(output_path):
    os.makedirs(output_path)


def _get_memory_stats():
    devices.torch_gc()
    torch.cuda.reset_peak_memory_stats()
    shared.mem_mon.monitor()
    return {k: -(v//-(1024*1024)) for k, v in shared.mem_mon.stop().items()}


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

    mem_stats = _get_memory_stats()
    vram = mem_stats['total'] / 1024
    low_vram = vram <= 12
    work_dir = work_folder(src_video)
    scaler = Scaler(low_vram)
    return scaler.process_video(src_video, work_dir, scale_factor, sampling_steps)


def interrupt():
    Scaler.interrupt_operation = True
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
