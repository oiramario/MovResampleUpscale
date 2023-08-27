import os
import subprocess

# python resample_series.py --input_path "F:\ai\test\output\4x-23_16_56\1-frames" --original_fps 30 --resampled_fps 60 --output_path "F:\ai\test\output\4x-23_16_56\60fps"
# python resequence_files.py --path "F:\ai\test\output\4x-23_16_56\60fps" --new_name "resampled@60fps" --rename

def series(input_path, output_path, original_fps, resampled_fps):
    ema_vfi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'usmodule', 'EMA-VFI-WebUI'))
    resample_path = os.path.join(ema_vfi_path, 'resample_series.py')
    args = ['python',
            resample_path, 
            '--input_path', input_path, 
            '--output_path', output_path, 
            '--original_fps', f'{original_fps}', 
            '--resampled_fps', f'{resampled_fps}',
            ]
    subprocess.run(args, cwd=ema_vfi_path)

    resequence_path = os.path.join(ema_vfi_path, 'resequence_files.py')
    args = ['python',
            resequence_path, 
            '--path', output_path, 
            '--new_name', 'resampled', 
            '--rename',
            ]
    subprocess.run(args, cwd=ema_vfi_path)
