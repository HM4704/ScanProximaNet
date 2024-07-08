## ScanProximaNet
This is a tool for displaying some infos about all the nodes of the Proxima (https://github.com/lunfardo314/proxima) test network.


## Installation
The following dependencies have to be installed (besides python3):

- sudo apt-get install libgtk-3-0 libgtk-3-dev
- pip install -r requirements.txt


## Usage
python ScanNetGui.py [-node start_node]


## Known Problems
In case this error occurs on start
"/bin/python3: symbol lookup error: /snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0: undefined symbol: __libc_pthread_init, version GLIBC_PRIVATE

issue the command "unset GTK_PATH"
