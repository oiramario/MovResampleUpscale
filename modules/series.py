import os
import subprocess


def restoration(input_path, output_path):
    vfi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'modules', 'VFIformer-WebUI'))
    restoration_path = os.path.join(vfi_path, 'interpolate_series.py')
    args = ['python',
            restoration_path, 
            '--input_path', input_path, 
            '--output_path', output_path, 
            '--depth', str(1),
            '--offset', str(2),
            ]
    subprocess.run(args, cwd=vfi_path)

    resequence_path = os.path.join(vfi_path, 'resequence_files.py')
    args = ['python',
            resequence_path, 
            '--path', output_path, 
            '--new_name', 'resynthesized_frame', 
            '--rename',
            ]
    subprocess.run(args, cwd=vfi_path)


def resample(input_path, output_path, original_fps, resampled_fps):
    vfi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'modules', 'VFIformer-WebUI'))
    resample_path = os.path.join(vfi_path, 'resample_series.py')
    args = ['python',
            resample_path, 
            '--input_path', input_path, 
            '--output_path', output_path, 
            '--original_fps', f'{original_fps}', 
            '--resampled_fps', f'{resampled_fps}',
            ]
    subprocess.run(args, cwd=vfi_path)

    resequence_path = os.path.join(vfi_path, 'resequence_files.py')
    args = ['python',
            resequence_path, 
            '--path', output_path, 
            '--new_name', 'resampled', 
            '--rename',
            ]
    subprocess.run(args, cwd=vfi_path)
