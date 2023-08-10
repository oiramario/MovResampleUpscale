import os
import subprocess

def upscale(grid_path, scale_grid_path):
    realesrgan = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'usmodule', 'realesrgan', 'realesrgan-ncnn-vulkan.exe'))

    args = [realesrgan, 
            '-i', grid_path, 
            '-o', scale_grid_path, 
            '-n', 'realesrgan-x4plus', 
            #'-n', 'realesr-animevideov3-x4', 
            '-j', '1:8:4',
            #'-x'
            ]
    subprocess.run(args)
