# mlx90640-bluetooth
Communicate with a mlx90640 thermal camera on a Raspberry Pi via bluetooth

Depends on https://github.com/pimoroni/mlx90640-library

The project has two parts, the server which runs on the Pi and uses python 2.7. The client runs on the host machine and displays a user interface, its written in python 3 and uses tkinter for graphics.

The server code depends on the mlx90640-library being installed in the `/home/pi` directory. 
The library needs to be compiled together with the python subdirectory. 

The server can be made to launch at boot time using the `mlxlauncher.sh` script. The following crontab line should work

    @reboot sh /home/pi/mlx90640-bluetooth/server/mlxlauncher.sh >> /home/pi/mlx90640-bluetooth/server/launcher.log 2>&1

The client needs some setup. The MAC address for the pi is hard coded in the client code `client/mlxclient.py`.

The client library relies on pybluez2 https://github.com/airgproducts/pybluez2/tree/master. Things seem to work better installing from source using
```
pip install git+https://github.com/airgproducts/pybluez2.git@0.46
```
