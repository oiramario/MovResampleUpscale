git submodule update --init --recursive
mkdir VFIformer\pretrained_models\pretrained_VFIformer
wget -P VFIformer\pretrained_models\pretrained_VFIformer https://huggingface.co/datasets/oiramario/VFIformer/resolve/main/net_220.pth
xcopy /S /E /Y "VFIformer\dataloader" "VFIformer-WebUI\dataloader\"
xcopy /S /E /Y "VFIformer\models" "VFIformer-WebUI\models\"
xcopy /S /E /Y "VFIformer\pretrained_models" "VFIformer-WebUI\pretrained_models\"
xcopy /S /E /Y "VFIformer\utils" "VFIformer-WebUI\utils\"

conda create -y -n mru python=3.10.9
conda activate mru
conda install pytorch==1.12.1 torchvision==0.13.1 -c pytorch
pip install -r VFIformer-WebUI\requirements.txt
pip install ffmpeg-python chardet
conda deactivate
