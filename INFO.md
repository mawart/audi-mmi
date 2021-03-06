Original code taken from: https://github.com/rampage128/arduinoMmi/

# Show/hide cursor
Discussed in: https://bluewavestudio.io/community/showthread.php?tid=596

Open command line and execute
`sudo bwscursor show`

# Changes to Rapsberry Pi Config
Open /boot/config.txt

Add the following lines to enable uarts 3-5

    [audi-mmi]
    dtoverlay=uart3
    dtoverlay=uart4
    dtoverlay=uart5

Debugging config issues:
https://blog.stabel.family/raspberry-pi-4-device-tree/

# Tools
https://pimylifeup.com/raspberry-pi-visual-studio-code/

# Remote Debugging
https://www.linkedin.com/pulse/python-remote-debugging-visual-studio-code-raspberry-pi-mircea-dogaru/

# Correct Pyhton linting errors on GPIO lib
https://stackoverflow.com/questions/56844378/pylint-no-member-issue-but-code-still-works-vscode

Press: CTRL + Shift + P

Click on "Preferences: Open Settings (JSON)"

Add this line into JSON : "python.linting.pylintArgs": ["--generate-members"]


# Open Auto Config
https://bluewavestudio.io/community/showthread.php?tid=593&pid=7208&highlight=openauto_controller_service#pid7208

Open /home/pi/.openauto/config/openauto_controller_service.ini

Change to the following:
    
    [Controller]
    Type=1
    Interface=/dev/ttyAMA0
    DoublePressSpeed=300

# HifiBerry DAC+ ADC PRO
Config change for Linux 5.4 (as used by OpenAuto Pro 10.0)

https://www.hifiberry.com/blog/configuration-changes-in-linux-5-4/
https://www.hifiberry.com/docs/software/configuring-linux-3-18-x/

Open /boot/config.txt

Add the following line to disable auto config of HifiBerry card

    force_eeprom_read=0

Remove the following line (if it exists) to disable onboard sound
    
    dtparam=audio=on

Add the following line to apply the correct device tree overlay

    dtoverlay=hifiberry-dacplusadcpro

Set output level

    $ amixer sset 'Master' 75%    

https://support.hifiberry.com/hc/en-us/community/posts/360003853669-DAC-Volume-Control-How-are-people-handling-

# Run program at startup

https://learn.sparkfun.com/tutorials/how-to-run-a-raspberry-pi-program-on-startup/all

Add the following to the /etc/rc.local file

    /usr/bin/python3 /home/pi/worspace/audi-mmi/main.py
    or
    sudo bash -c '/usr/bin/python3 /home/pi/worspace/audi-mmi/main.py > /home/pi/worspace/audi-mmi/main.log 2>&1' &

https://www.tecmint.com/auto-execute-linux-scripts-during-reboot-or-startup/

# Set level of HifiBerry DAC+ ADC PRO

Currently (10-10-2020) storing and restoring alsa sound settings does not work on 
the Raspbian release used by OpenAuto. To set the sound level to 75% at startup 
(to prevent overdriving the input of the Audi TV-Tuner) we use a startup script with the following
content:

	amixer set Master 75%

# Communication

PASSTHROUGH MODE ON:

MMI Head Unit (Tx) --------------------------------------------------------------------------------> (Rx) MMI Button Control
MMI Button Control (Tx) ---------------------------------------------------------------------------> (Rx) MMI Head Unit


PASSTHROUGH MODE OFF:

MMI Head Unit --------------------------------------------------------------------------------> MMI Button Control

MMI Button Control ---- if Media Btn is pressed then -----------------------------------------> MMI Head Unit
                            Enter Media mode
                        else if Next Btn is pressed when in Media mode
                            Enter OpenAuto mode
                        else if Other Btn is pressed when in Media mode or OpenAuto mode
                            Leave OpenAuto mode
                            Leave Media mode

MMI Button Control ---- if OpenAuto mode then ------------------------------------------------> MMI Head Unit
                            Intercept all btn events from MMI Button Control
                              and send them to OpenAuto serial inteface
                            Forward all other data to MMI Head Unit
                            For every intercepted event send next btn event to 
                              MMI Head Unit to get a response from MMI Head Unit
                        else 
                            Forward all data to MMI Head Unit 
