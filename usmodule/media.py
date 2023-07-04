import os

import ffmpeg


def extract(media_probe, media_path, frames_path, audio_path):
    # extract streams from media
    input_media = ffmpeg.input(media_path)
    output_streams = [input_media.output(os.path.join(frames_path, '%05d.png'))]
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


def merge(media_probe, frames_path, frame_rate, audio_path, output_media_file):
    # merge streams to media
    input_streams = [ffmpeg.input(os.path.join(frames_path, '%05d.png'), framerate=frame_rate)]
    audio_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'audio'), None)
    if audio_stream:
        input_streams.append(ffmpeg.input(os.path.join(audio_path, 'audio.mp3')))
    input_args = ['-hide_banner']
    (
        ffmpeg
        .output(*input_streams, output_media_file, vcodec='libx264', pix_fmt='yuv420p', crf=18)
        .overwrite_output()
        .global_args(*input_args)
        .run()
    )
