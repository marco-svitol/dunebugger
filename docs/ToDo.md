
# Add-ons
## Motor
Review, debug, improve
## Arduino
### To control AC dimming board
Review, test
### As a HUB to run less cables from the RPI
Design, test, pro/cons
## Local MCU (ESP32) at the switch → MQTT to Raspberry Pi
Design, test

# Dunebugger core 
See add-ons
Scheduler will require minimal develop here as well

# Dunebugger remote
Just needs updates to handler new features as Scheduler, UI features
Maybe can be more parametric and load messagin queue rules/routes from config

# Dunebugger scheduler
Redo from scratch, is too convoluted right now
Config format based on requirement:
Recurrent, special days, quiet periods, 

# Dunebugger terminal
Seems fine

# Web Interface
## Main
Add Device info as uptime, temperature, location, wifi name, hotspot name
## Sequence
Upload sequence
Change Row names
Modify Sequence 
Upload music and sfx and choose sfx

# GPIOs
Move Logs to dedicated section
Remove Start/stop ?

## Scheduler
From scratch
## Analytics
total runs, runs distribution, total hours of running, device uptime and device info

# "Logs" or "System" (new)
Show all logs from Dunebugger Core
Set Log verobisty
Switch off/on Web logs (save Websocket messages)
Get other RPI logs?
Manage some system stuf?

# RPI
Two WiFi interfaces: a Hotspot to allow initial config and the other to connect to WiFi
Time -> get time from another component? or directly via internet?
Voltage check
Updates automation
