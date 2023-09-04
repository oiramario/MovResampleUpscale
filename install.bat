git submodule update --init --recursive
mkdir VFIformer\pretrained_models\pretrained_VFIformer
wget -P VFIformer\pretrained_models\pretrained_VFIformer https://huggingface.co/datasets/oiramario/VFIformer/resolve/main/net_220.pth
xcopy /S /E /Y "VFIformer\dataloader" "VFIformer-WebUI\dataloader\"
xcopy /S /E /Y "VFIformer\models" "VFIformer-WebUI\models\"
xcopy /S /E /Y "VFIformer\pretrained_models" "VFIformer-WebUI\pretrained_models\"
xcopy /S /E /Y "VFIformer\utils" "VFIformer-WebUI\utils\"

conda create -y -n mru python=3.10.9
conda activate mru
pip install gradio chardet ffmpeg-python opencv-python
pip install torch==1.13.1 tensorboardX==2.6 torchvision==0.14.1 timm==0.6.12
conda install pytorch==1.12.1 torchvision==0.13.1 -c pytorch
conda deactivate
