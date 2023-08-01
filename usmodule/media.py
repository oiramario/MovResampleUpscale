import os
import urllib.request

import ffmpeg
from tqdm import tqdm


def download(url, dir):
    name = os.path.basename(url)
    path = os.path.join(dir, name)
    if not os.path.exists(path):
        request = urllib.request.urlopen(url)
        total = int(request.headers.get('Content-Length', 0))
        with tqdm(total=total, desc=f'Downloading: {name}', unit='B', unit_scale=True, unit_divisor=1024) as progress:
            urllib.request.urlretrieve(url, path, reporthook=lambda count, block_size, total_size: progress.update(block_size))

def check():
    sd_root = os.getcwd()
    sd_models = os.path.join(sd_root, 'models', 'Stable-diffusion')
    download('https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.safetensors', sd_models)
    sd_vae = os.path.join(sd_root, 'models', 'VAE')
    download('https://huggingface.co/oiramario/StableSR/resolve/main/vqgan_cfw_00011_vae_only.ckpt', sd_vae)
    sr_models = os.path.join(sd_root, 'extensions', 'sd-webui-stablesr', 'models')
    download('https://huggingface.co/Iceclear/StableSR/resolve/main/webui_768v_139.ckpt', sr_models)


def extract(media_probe, media_path, frames_path, audio_path=None, scale_factor=None):
    # extract streams from media
    input_media = ffmpeg.input(media_path)
    if scale_factor:
        video_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'video'), None)
        width = video_stream['width']
        height = video_stream['height']
        target_width = int(width * scale_factor)
        target_height = int(height * scale_factor)
        # if the target width is not dividable by 8, then round it up
        if target_width % 8 != 0:
            target_width = target_width + 8 - target_width % 8
        # if the target height is not dividable by 8, then round it up
        if target_height % 8 != 0:
            target_height = target_height + 8 - target_height % 8
        input_media = input_media.filter('scale', width=target_width, height=target_height)
    output_streams = [input_media.output(os.path.join(frames_path, '%05d.png'), start_number=0, r=24)]
    if audio_path:
        audio_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_stream:
            output_streams.append(input_media.output(os.path.join(audio_path, 'audio.mp3')))
    if len(output_streams) > 1:
        output_node = ffmpeg.merge_outputs(*output_streams)
    else:
        output_node = output_streams[0]
    output_args = ['-hide_banner']
    (
        output_node
        .overwrite_output()
        .global_args(*output_args)
        .run()
    )


def merge(media_probe, frames_path, audio_path, output_media_file):
    # merge streams to media
    input_streams = [ffmpeg.input(os.path.join(frames_path, '%05d.png'), framerate=24)]
    audio_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'audio'), None)
    if audio_stream:
        input_streams.append(ffmpeg.input(os.path.join(audio_path, 'audio.mp3')))
    input_args = ['-hide_banner']
    (
        ffmpeg
        .output(*input_streams, output_media_file, vcodec='libx264', pix_fmt='yuv420p')
        .overwrite_output()
        .global_args(*input_args)
        .run()
    )
