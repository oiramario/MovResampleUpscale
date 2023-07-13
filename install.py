import os
from launch import git_clone, is_installed, run_pip


def main():
    packages = [
        'webuiapi',
        'ffmpeg'
    ]
    for m in packages:
        try:
            if not is_installed(m):
                run_pip(f'install {m}', f'mov-scale: {m}')
        except Exception as e:
            print(e)

    sd_root = os.getcwd()
    sd_extensions = os.path.join(sd_root, 'extensions')

    git_clone('https://github.com/pkuliyi2015/sd-webui-stablesr.git', 
              os.path.join(sd_extensions, 'sd-webui-stablesr'), "StableSR")
    git_clone('https://github.com/pkuliyi2015/multidiffusion-upscaler-for-automatic1111.git', 
              os.path.join(sd_extensions, 'multidiffusion-upscaler-for-automatic1111'), "Tiled Diffusion & VAE")
    

if __name__ == "__main__":
    main()
