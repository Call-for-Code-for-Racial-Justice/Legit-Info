export USE_SQLITE3='False'
export PATH=/home/vcap/.local/bin:$PATH
echo "Current Working Directory: " $PWD 
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
python3 -m pip install pipenv
pipenv install
