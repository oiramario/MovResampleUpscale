import os
import subprocess


def upscale(input_path, output_path, animvideo):
    realesrgan = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'modules', 'realesrgan', 'realesrgan-ncnn-vulkan.exe'))
    model = 'realesr-animevideov3-x4' if animvideo else 'realesrgan-x4plus'

    args = [realesrgan, 
            '-i', input_path, 
            '-o', output_path, 
            '-n', model, 
            '-j', '1:8:4',
            #'-x'
            ]
    subprocess.run(args)
