from launch import git_clone, is_installed, run_pip


def main():
    print('mov-scale running...')
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


if __name__ == "__main__":
    main()
