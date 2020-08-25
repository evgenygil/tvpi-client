# Raspberry Pi media signage system

## Installation

* Install Raspbian OS Lite (latest: Buster)
* `sudo raspi-config` (change password, wifi, ssh, set console autologin, locale)
* `sudo apt-get update` `sudo apt-get upgrade`
* Clone project `git clone https://github.com/evgenygil/tvpi-client.git`
* Get into `~/tvpi-client` and run `./install.sh` (`sudo chmod +x install.sh` if you have permission error)
* Run service with `node ~/tvpi-client/build/index.js`

* For autostart you can run it simple as service or use any software, below is pm2 example
```
sudo npm install pm2 -g

sudo pm2 startup // use command from result

pm2 start <index.js path>
pm2 save

sudo reboot
```

* For Stretch Pi version install `kweb_upgrade_stretch_20190408.tar.gz` package from `arc`
```
tar -xzf kweb_upgrade_stretch_20190408.tar.gz
cd kweb_upgrade_stretch_20190408
./install
```

### Articles
https://die-antwort.eu/techblog/2017-12-setup-raspberry-pi-for-kiosk-mode/
https://www.raspberrypi.org/forums/viewtopic.php?f=66&t=40860
