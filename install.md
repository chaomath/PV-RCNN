## Installation

Tested in environment:
- Conda
- torch 1.4
- CUDA 10.1
- Ubuntu 18.04
- Python 3.7

1. Installing Pointnet2:
```
git clone https://github.com/sshaoshuai/Pointnet2.PyTorch.git
cd Pointnet2.PyTorch && python setup.py install
export PYTHONPATH=$PYTHONPATH:/path/to/Pointnet2.PyTorch/
```

2. Installing patched spconv:
```
git clone https://github.com/jhultman/spconv.git --recursive
cd spconv && python setup.py bdist_wheel
cd ./dist && pip install *.whl
```

3. Installing torchsearchsorted:
```
git clone https://github.com/aliutkus/torchsearchsorted.git
cd torchsearchsorted && pip install .
```

4. Installing misc python packages:
```
pip install -r requirements.txt
```

5. Installing pvrcnn (this package):
```
python setup.py develop
```
