import ffmpeg
import os
import datetime

def process_video(media_path, output_path, scale, steps):
    if not os.path.isfile(media_path) or not os.path.isdir(output_path):
        return

    # stream infomation
    media_probe = ffmpeg.probe(media_path, hide_banner=None) # , count_frames=None
    video_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'video'), None)
    if not video_stream:
        return
    time = float(video_stream['duration']) // 2
    width = video_stream['width']
    height = video_stream['height']
    frame_rate = eval(video_stream['avg_frame_rate'])
    count_frames = None if 'nb_read_frames' not in video_stream else int(video_stream['nb_read_frames'])

    # extract streams from media
    frames_path = os.path.join(output_path, 'frames')
    if not os.path.exists(frames_path):
        os.makedirs(frames_path)
    input_media = ffmpeg.input(media_path)
    output_streams = [input_media.output(os.path.join(frames_path, '%05d.png'))]
    audio_stream = next((stream for stream in media_probe['streams'] if stream['codec_type'] == 'audio'), None)
    if audio_stream:
        output_streams.append(input_media.output(os.path.join(output_path, 'audio.mp3')))
    if len(output_streams) > 1:
        output_node = ffmpeg.merge_outputs(*output_streams)
    else:
        output_node = output_streams[0]
    output_args = ['-hide_banner']
    output_node.overwrite_output().global_args(*output_args).run()

    # 
    current = f'{scale}x-{datetime.datetime.now().strftime("%H_%M_%S")}'
    output_media_path = os.path.join(output_path, current)
    if not os.path.exists(output_media_path):
        os.makedirs(output_media_path)

    # merge streams to media
    input_streams = [ffmpeg.input(os.path.join(frames_path, '%05d.png'), framerate=frame_rate, pix_fmt='yuv420p')]
    if audio_stream:
        input_streams.append(ffmpeg.input(os.path.join(output_path, 'audio.mp3')))
    input_args = ['-hide_banner']
    (
        ffmpeg
        .output(*input_streams, os.path.join(output_path, '5.mp4'), vcodec='libx264', pix_fmt='yuv420p') # , crf=18
        .overwrite_output()
        .global_args(*input_args)
        .run()
    )

process_video(r'F:\ai\test\abc.mp4', r'F:\ai\test', 2.0, 20)
