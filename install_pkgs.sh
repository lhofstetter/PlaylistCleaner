pip --version
if [ $? -eq 0 ]; then
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python get-pip.py
fi

pip install spotipy
pip install argparse
