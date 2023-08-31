import os
import os.path
import pathlib
from datetime import datetime

import gradio as gr

from scaler import process_video

# directory of the outputs
sd_path = pathlib.Path().absolute()
output_path = os.path.join(sd_path, 'outputs')
if not os.path.exists(output_path):
    os.makedirs(output_path)


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


def generate(src_video, restoration, animvideo):
    if not src_video:
        return

    work_dir = work_folder(src_video)
    return process_video(src_video, work_dir, restoration, animvideo)


if __name__ == "__main__":
    with gr.Blocks(analytics_enabled=False) as mov_upscale_interface:
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    src_video = gr.Video(interactive=True, include_audio=True, label='Source')
                with gr.Row():
                    with gr.Column():
                        restoration = gr.Checkbox(label='Frame Restoration')
                    with gr.Column():
                        animvideo = gr.Checkbox(label='Is Animation')
                with gr.Row():
                    btn_generate = gr.Button('Generate', variant='primary')
            with gr.Column():
                with gr.Row():
                    dst_video = gr.Video(interactive=False, include_audio=True, label='Target')
                with gr.Row():
                    btn_open_folder = gr.Button('Open Folder')
                    btn_save = gr.Button('Save Video')
                with gr.Row():
                     download_file = gr.File(None, interactive=False, show_label=False, visible=False)

        btn_generate.click(
            fn=generate, 
            inputs=[src_video, restoration, animvideo], 
            outputs=dst_video, 
            show_progress=True)

        btn_open_folder.click(
            fn=lambda x, y: os.startfile(work_folder(x)) if x and y else None,
            inputs=[src_video, dst_video])

        btn_save.click(
            fn=lambda x: gr.File.update(value=x, show_label=True, visible=True) if x else None,
            inputs=dst_video,
            outputs=download_file)

        mov_upscale_interface.launch()
