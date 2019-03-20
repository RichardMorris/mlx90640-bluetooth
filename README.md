# mlx90640-bluetooth
Communicate with a mlx90640 thermal camera on a Raspberry Pi via bluetooth

Depends on https://github.com/pimoroni/mlx90640-library

The project has two parts, the server which runs on the Pi and uses python 2.7. The client runs on the host machine and displays a user interface, its written in python 3 and uses tkinter for graphics.


The server can be made to launch at boot time using the mlxlauncher.sh script. The following crontab line should work
@reboot sh /home/pi/mlx90640-bluetooth/server/mlxlauncher.sh >> /home/pi/mlx90640-bluetooth/server/launcher.log 2>&1
