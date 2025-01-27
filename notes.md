
### crontab -e
```@reboot tmux new -d -s cycle -c '/home/pi/dunebugger/app' 'python /home/pi/dunebugger/app/switchonoff.py''```

### niceToHave:
- timing random con range di variabilità da aggiungere a funzione sleep
- cicli multipli scelta random
- WEBGUI -> velocità + contatori + calendario/orari messe + programciclo...


### install rpi notes (use with care)
```
sudo apt update -y; sudo apt upgrade -y
sudo apt install git tmux speedtest-cli -y    
git clone https://github.com/marco-svitol/dunebugger.git     

# create key pair for github
ssh-keygen -t ed25519 -C "marco.cambon@gmail.com"
# go to GitHub and create pub key for this raspberry
# test connection with ssh -T git@github.com

#Bad experience in upgrading Python to latest verision, I would avoid it. But here's the steps I took:
				#Python pre-requisites:
				sudo apt install -y libbz2-dev libffi-dev libncurses-dev libreadline-dev libssl-dev zlib1g-dev
				sudo apt-get install libsqlite3-dev libdb-dev libgdbm-dev liblzma-dev tk-dev uuid-dev

				#Python replace 3.13.0 with the latest version found at:
				# https://www.python.org/downloads/
				export PYTHON_VERSION=3.13.0
				wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz
				tar -xvf Python-$PYTHON_VERSION.tgz
				cd Python-$PYTHON_VERSION
				./configure --prefix=/usr/local/Python-$PYTHON_VERSION
				make
				sudo make install

				#set python default command
				sudo rm /usr/local/bin/python3
				sudo cp /usr/local/Python-$PYTHON_VERSION/* /usr/local/bin
				cd /usr/local/bin
				sudo ln -s /usr/local/bin/python3.13 python3
				sudo ln -s /usr/local/bin/python3.13 python
				sudo ln -s /usr/local/bin/pip3.13 pip

sudo apt install vlc

# run 
sudo raspi-config
# and check settings:
# mandatory: enlarge filesystem in "Advanced Options"

#manage network through NetworkManager: nmcli / nmtui
sudo nmcli connection add type wifi ifname wlan0 con-name Casa ssid "Casa"
sudo nmcli connection modify Casa wifi-sec.key-mgmt wpa-psk wifi-sec.psk "D0ntW0rry2016!"
sudo nmcli connection modify Casa +ipv4.addresses 192.168.1.225
sudo nmcli connection modify Casa +ipv4.gateway 192.168.1.254
sudo nmcli connection modify Casa +ipv4.dns "192.168.1.254"
sudo nmcli connection modify Casa +ipv4.dhcp-timeout 20
sudo nmcli connection modify Casa ipv6.method "disabled"

sudo nmcli connection add type wifi ifname wlan0 con-name Rosetum ssid "Rosetum"
sudo nmcli connection modify Rosetum wifi-sec.key-mgmt wpa-psk wifi-sec.psk "mozart@19A"
sudo nmcli connection modify Rosetum +ipv4.addresses 10.10.10.20
sudo nmcli connection modify Rosetum +ipv4.gateway 10.10.10.1
sudo nmcli connection modify Rosetum +ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli connection modify Rosetum +ipv4.dhcp-timeout 20
sudo nmcli connection modify Rosetum ipv6.method "disabled"

# optional : add your id_rsa.pub to authorized_keys to access to ssh without password

# to fix keyboard arrows
sudo apt install vim 

# copy .vimrc


#Troubleshoot 
apt install shows  "apt_pkg" missing
solution:
sudo ln -s apt_pkg.cpython-311-arm-linux-gnueabihf.so apt_pkg.so

#create ~/.config/pip/pip.conf :
[global]
break-system-packages = true


#AP
sudo nmcli con add con-name hotspot ifname wlan1 type wifi ssid "dunebugger"
sudo nmcli con modify hotspot wifi-sec.key-mgmt wpa-psk
sudo nmcli con modify hotspot wifi-sec.psk "Shish2018"
sudo nmcli con modify hotspot 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
```


