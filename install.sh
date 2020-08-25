#!/bin/sh
echo "Installing X utils..."
sudo apt-get -y install xserver-xorg x11-xserver-utils xinit openbox

echo "Installing chromium-browser..."
sudo apt-get -y install chromium-browser

if [ ! -f /usr/bin/gdebi ]
then
echo "Installing gdebi-core..."
sudo apt-get -y install gdebi-core
fi

echo "Installing kweb suite..."
sudo gdebi -n lib/kweb_1.7.9.8-2_armhf.deb

if [ -f /usr/local/bin/omxplayergui ]
then
echo "Installing updates..."
sudo cp lib/omxplayergui /usr/local/bin
sudo cp lib/kwebhelper.py /usr/local/bin
sudo cp lib/kwebhelper_set.py /usr/local/bin
sudo cp lib/ytdl_server.py /usr/local/bin
echo "Installing gksu..."
sudo gdebi -n lib/libgtop-2.0-10_2.34.2-1_armhf.deb
sudo gdebi -n lib/libgksu2-0_2.0.13~pre1-9_armhf.deb
sudo gdebi -n lib/gksu_2.0.2-9_armhf.deb
else
echo "Kweb suite must have been installed before it can be updated"
fi

echo "Writing startup config..."
touch ~/.bash_profile
echo "[[ -z \$DISPLAY && \$XDG_VTNR -eq 1 ]] && startx -- -nocursor" > ~/.bash_profile

echo "Copying autostart configuration..."
sudo cp config/autostart /etc/xdg/openbox/

echo "Copying boot configuration..."
sudo cp config/config.txt /boot/

echo "Installing NodeJS..."
curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "Installing and building project..."
cd ~/tvpi && npm i && npm run build

echo "Successfully installed! Please configure service autostart and reboot to apply changes."
