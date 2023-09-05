git submodule update --init --recursive

call conda.bat create -y -n mru python=3.10.9
call conda.bat activate mru
pip install clint gradio chardet ffmpeg-python opencv-python torch==1.13.1 tensorboardX==2.6 torchvision==0.14.1 timm==0.6.12
call conda.bat install -y pytorch==1.12.1 torchvision==0.13.1 -c pytorch

mkdir VFIformer\pretrained_models\pretrained_VFIformer
python download.py "https://huggingface.co/datasets/oiramario/VFIformer/resolve/main/net_220.pth" "VFIformer\pretrained_models\pretrained_VFIformer"

xcopy /S /E /Y "VFIformer\dataloader" "VFIformer-WebUI\dataloader\"
xcopy /S /E /Y "VFIformer\models" "VFIformer-WebUI\models\"
xcopy /S /E /Y "VFIformer\pretrained_models" "VFIformer-WebUI\pretrained_models\"
xcopy /S /E /Y "VFIformer\utils" "VFIformer-WebUI\utils\"

call conda.bat deactivate
