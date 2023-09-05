import sys
from os import path

import requests
from clint.textui import progress


def download(url, output):
    with requests.get(url, stream=True, allow_redirects=True) as r:
        file_name = path.basename(url)
        with open(path.join(output, file_name), 'wb') as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in progress.bar(r.iter_content(chunk_size=1024), label=f'{file_name}: ', expected_size=(total_length / 1024) + 1):
                if chunk:
                    f.write(chunk)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        url = sys.argv[1]
        output = sys.argv[2]
        download(url, output)
