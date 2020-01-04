# Mouse tracking and analysis online

Large scale mouse tracking experiment with edge computing.

## Board

Sipeed [Maix Dock](https://wiki.sipeed.com/en/maix/board/dock.html)

## Setup

1. Setup application server
```bash
python manage.py migrate
python manage.py createsuperuser
```
2. Run application server
```bash
python manage.py runserver
```
3. Setup devices: Change SSID, password and device name in NPU/slave.py, then upload it to the board.
4. Once the board is connected to the internet, the device will appear at the application server.
5. Prepare devices: place the slave at the desired location.
6. Run experiment: create an experiment on the application server, and assign the device to the experiment.

## Credit

- [rad2](https://hackaday.io/project/168588-rad2-research-activity-detector-version-2)
