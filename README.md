# Lizard Pi RFID Camera Trap

This is full documentation for the Raspberry Pi project, from downloading the Raspberry Pi OS to the physical components that we are working with on our Raspberry Pi. If your components are different from ours, you may have to take different steps to achieve the same results we achieved.

# What this project does

This project was created in order to monitor Eastern collared lizards (*Crotaphytus collaris*) and their movements. We used this specific trap due to how cheap it can be and how modifiable it can be with the right amount of work. Some projects that use RFID and Raspberry Pis require handling of the animal each time it is scanned, but this bypasses that with the copper loop being outside of a board. By creating this project and troubleshooting it, we have made something that collects environmental data, RFID ID numbers, time, date, and photos of the lizards with the RFID tags. This project has also gone further, as it has a motion camera which can be helpful in catching photos of other animals.

## Codes and their purposes

This github had four different codes, HourlyBMESPI.py, HourlyClimateReaderI2C.py, MotionDetection\_20261022.py, and RFID\_BME\_RTC\_20261022.py. These codes work together to create accurate data sets for projects that need RFID, pictures, environmental data, and accurate time.

HourlyBMESPI.py uses multiple packages to create a one-time read of the current environment (temperature, humidity, and pressure) and puts that data into a .csv file that has all of that information as well as time and date. This specific code is used for a BME that is connected to a raspberry pi with the SPI pins, not the I2C pins. This is to get around the Real Time Clock (RTC) module connections.

The HourlyClimateReaderI2C.py also does what the HourlyBMESPI.py does, but only when the BME is connected to the pi using the I2C pins. The resulting .csv file will still have time and date embedded in it, but it will need to be checked for accuracy.

The MotionDetection\_20261022.py uses some different packages from the two BME codes, as it uses a camera. This code uses cv2 and picamera2 packages to use the connected camera. The pi takes a picture every couple of seconds using this code and parses out differences in the pixel color. If they are different enough, the pictures are saved in a folder that this code creates.

The RFID\_BME\_SPI\_20261022.py code uses an RFID module to detect and record RFID tag IDs as well as a camera to take pictures when this code is triggered. Not only does it take those pictures and record the IDs, it also uses components from the HourlyBMESPI.py to record the environmental data at that specific time. All of the textual information is saved to a .csv file and all the pictures go into a folder where they can be easily found.

# Raspberry Pi Setup

## Downloading the Raspberry Pi Operating System (OS) onto a Raspberry Pi 5

The OS used for our raspberry pis (pis, or pis) is the Debian Trixie version. To get this onto your pi, you will need to use a microSD card reader that can run on your personal computer. After that is acquired you will need to install the pi imager to your computer from this link: https\://www\.raspberrypi.com/software/. This will guide you to the official pi website that holds their software that they have developed for pi needs. Install the imager and create a shortcut on the desktop for ease of use. Open the application and click yes to allow it to write to your hard drive. This allows the program to access the microSD card that is connected to your pc. Once it opens, it will prompt you to pick an pi model, click pi 5\. Then the choices of OS for your pi will pop up, scroll until you see Raspberry Pi OS (64-bit). This option should say \`Debian Trixie\` in the description. This will lead you to choose a storage device for this particular program, pick your microSD card. Skip all of the customization, as it is not needed and then allow the imager to write the program onto the microSD card. Once done, eject the microSD card and insert it into the pi.

## Starting the pi and configuring it to our needs

Once the pi is plugged into a monitor, a power source and a mouse and keyboard, it will prompt the set up stage of the pi. This includes creating an account for the information to live, a password (this needs to be written down, but will most likely not be used for the remainder of the project unless you turn on admin password), and downloading any current updates. After it updates it will have to restart, but then the pi should be set up for the next steps.

Click the command prompt in the top left corner of the screen (should look like a black rectangle with a blue bar at the top). This will open a command prompt for you to download, configure and test some aspects of our pi. The command prompt is the primary tool we use for this as it bypasses the need of website downloads and it gets all of the packages from certain pi approved libraries. There may be a couple of cases that we do use a website download; however this is usually from a trusted github. *As this goes, things that need to be typed into the command prompt will be indented beneath specific instructions or steps.*

- sudo raspi-config

This command allows us to get into the configuration tool for our needs, technically this can be done a different way, however this way makes sure the entire pi is configured correctly. Once into the menu, scroll down to the interface options. This will have multiple options to enable and disable. Three things need to be enabled for our pis, the SPI, the I2C and the Serial Port.

Next you will need to change the externally managed file in the filesystem root. This takes a little bit of finding, but hopefully it will be where it is supposed to be.

Go into your file manager by clicking the file icon in the top left corner. This will open in your home folder, you need to be in your Filesystem Root. Filesystem Root should be an option at the top left of the file manager window, click it. Once inside, you should see 19 folders, click the folder labeled \`lib\`. Then scroll all the way down to the folder that is named \`python3.13\` (your version of python may be different, but the folder should still be in relatively the same spot). This folder will have many .txt files, find both files with the name \`EXTERNALLY-MANANGED\`. They will both be a .txt file, however one will have .orig and one will not. We have to rename the file without the .orig to allow the user to download some of the python packages using pip (talked about later). To rename this file, you have to go back to the command prompt and type:

- sudo mv /lib/*python3.13*/EXTERNALLY-MANAGED /lib/*python3.13*/EXTERNALLY-MANAGED-OLD
  - /file/path in this case is the path you clicked on to get to the original file (this can be easily obtained by right clicking the folder and selecting copy path, then right clicking the command prompt and pasting, ctrl \+ v does not work in the command prompt for pasting)  
  - python3.13 may not be your specific version of python, check and make sure of your version and type in that version

Finally, we need to change the config file (different from the raspi-config command). This needs to be changed to your specific camera, watchdog, UART, and bluetooth needs. To change this file you will need to enter back into a command terminal, then type:

- Sudo nano /boot/firmware/config.txt

This will put you into a .txt file editor. Go to the \[all\] subtitle and add the following:

- dtoverlay=imx708

  - Use \`dtoverlay=imx708,cam0\` if the arducam is connected through the CAM0 port. The cam0 addition is not needed for the pi3s and pi4s, as they only have one camera port.

Under \`\# Automatically load overlays for detected cameras\` change the \`camera\_auto\_detect=1\` to \`camera\_auto\_detect=0\`, as the pi 5 does not correctly autodetect arducam imx708.

- Type these commands exactly how they are here, or they will not work (this includes not typing in the spaces)

We need to turn on watchdog. Watchdog comes preinstalled with Trixie 13\. We use this tiny package to watch over the pi, so if the pi freezes we do not need to manually restart it. This package uses a two-line command in the system config file to time how long it takes to send a small signal. If the interval reaches a specific time, it will reboot the pi automatically, allowing the pi to continue to work without manual intervention.

Scroll all the way to the end of the file (under the previous dtoverlay command) and type:

- dtparam=watchdog=on

Then save and exit the file. After that you need to reboot your pi again to set the change. Next we need to get into the system.conf file, which is different from the config.txt file.

- sudo nano /etc/systemd/system.conf

Scroll to the two lines that read:

- \`RuntimeWatchdogSec=\`  
- \`ShutdownWatchdogSec=10min\`

These lines need to be uncommented (delete the \#) to work properly. The Shutdown command should not be edited other than deleting the \#, but you will need to add a Runtime. Raspberry Pis cannot handle a time longer than 15 seconds for the Runtime section, so it is recommended that the signal be set to either 10 or 15 seconds.

- RuntimeWatchdogSec=15

Save your file, then go back into your command terminal and type:

- sudo systemctl daemon-reexec

This allows watchdog to run without having to reboot your pi. You can also test if this by running a command that will force a system panic (safe to do if everything is saved and closed). This command is built into trixie to test the pi.

- sudo sh \-c \`echo c \> /proc/sysrq-trigger\`

After that runs and your pi restarts, you can run this command to verify the reboot cause:

- sudo journalctl \-b 0 \| grep \-i \`watchdog\`

Once your Pi is rebooted it should have all the necessary things set up to start downloading packages to make the peripherals work. This will also allow you to test the camera since you’ve fully rebooted the pi. If you’d like to test it you can go into the command terminal and type:

- Rpicam-hello

This gives you a live preview of the camera, indicating that it is fully operational.

## Packages that are needed for this project

Currently, the packages that are needed for this project are:

- RPi.bme280 package
  - For the environmental sensor  
- Cv2 package
  - For the motion camera

## Downloading packages

First we will be downloading RPi.bme280 through the command terminal.
- pip3 install RPi.bme280
  - This is to make our temperature sensor work, and should not require any additional terminal commands
Then we can install the cv2 package.
- pip3 install opencv-python
  - This is to make our temperature sensor work, and should not require any additional terminal commands

## Setting up the .service file

To get the code to work on start up, you then need to create and implement two .service files, one for the RFID code and one for the Motion Camera code. We will be creating both of these files through the command line.

- sudo nano /etc/systemd/system/MotionCamera.service

In the .service file you will need to type these things in this order, with no changes:

- \[Unit\]  
- Description=motion camera code startup
  - This is only needed for your benefit, so input what you think is needed  
- After=multi-user.target systemd-module-load.service  
- Wants=systemd-modules-load.service  
- \[Service\]  
- Type=simple  
- User=YOURUSER
  - Your user is at the top of the command line if you do not remember  
- WorkingDirectory=/home/YOURUSER  
- ExecStart=/usr/bin/python3 /home/YOURUSER/PATH/TO/FILE/MotionDetection.py  
- Restart=on-failure  
- RestartSec=5  
- Environment=DISPLAY=:0  
- Environment=XAUTHORITY=/home/YOURUSER/.Xauthority  
- Environment=QT\_QPA\_PLATFORM=offscreen  
- \[Install\]  
- WantedBy=multi-user.target	

Then press control and X, enter, Y, and enter again to save and exit the .service file. We will do the same thing, with minor changes, for the RFID .service file:

- sudo nano /etc/systemd/system/RFIDcode.service

In the .service file you will need to type these things in this order, with no changes:

- \[Unit\]  
- Description=motion camera code startup
  - This is only needed for your benefit, so input what you think is needed  
- After=multi-user.target systemd-module-load.service  
- Wants=systemd-modules-load.service  
- \[Service\]  
- Type=simple  
- User=YOURUSER
  - Your user is at the top of the command line if you do not remember
- WorkingDirectory=/home/YOURUSER  
- ExecStart=/usr/bin/python3 /home/YOURUSER/PATH/TO/FILE/RFID.py  
- Restart=on-failure  
- RestartSec=5  
- Environment=DISPLAY=:0  
- Environment=XAUTHORITY=/home/YOURUSER/.Xauthority  
- Environment=QT\_QPA\_PLATFORM=offscreen  
- \[Install\]  
- WantedBy=multi-user.target

Again, save and exit the file to the command line.

Now we need to implement the files and make sure they are running. To do this, we will use a couple of commands in the terminal.

- sudo systemctl daemon-reload  
- sudo systemctl enable MotionCamera.service  
- sudo systemctl start MotionCamera.service  
- sudo systemctl status MotionCamera.service  
- sudo systemctl enable RFIDcode.service  
- sudo systemctl start RFIDcode.service  
- sudo systemctl status RFIDcode.service

This will start up your .service files and allow them to work. The status commands are to check if your codes are functional and working currently. If they are working, then on each start up of the pi, the RFID code and the MotionCamera code should be on.

## Setting up the Crontab for the Hourly BME code

The HourlyBME.py unfortunately cannot be set up using the .service files, but it can be set up to run through a crontab.

- sudo nano crontab \-e

In the crontab, you will need to scroll down to the area where it has the example of how to set up a file to run. In that area, this is what you will type:

- @hourly /usr/bin/python3 /home/YOURUSER/PATH/TO/FILE/HourlyBME.py

This will automatically set up when you reboot your pi. Since it is an hourly script, you will have to wait until the hour turns over to check if the crontab worked.

## Physical setup for the components of the pi

Now that you have all the software needed for pi, it’s time for the RFID reader and temperature sensor to be plugged in. Also note that anything that is bulleted is not a piece of code, rather it is the connections to and from the pi and components.

Here is a link to the official Vilros site (https://vilros.com/) (verified Raspberry pi seller) that has a printable PDF of the Pi 5 Pinout. This is useful to look back on in the next couple of steps and to have handy for repetition of building multiple traps.

For the RFID Reader you will need 3 wires, either 3 coated wires that you need to solder to the board, or the female to female wires (the female to female wires are recommended for ease of use). The RFID copper loop already has two wires that are female, therefore there is no need to grab extra wires for it.

- The wires for the copper loop need to connect on the RFID board (not the pi) at pins \`ANT1\` and \`ANT2\`. It does not matter which wire goes to which pin.  
- Pin \+5-9v on the reader needs to connect to pin 2 on the pi (this is the 5 volt pin)  
- Pin 3.3vTX on the reader needs to connect to pin 10 on the pi (this is the GPIO15, RXD pin)  
- GND (ground) on the reader is connected to pin 6 on the pi (this is ground on the pi as well)

If you are using the 9V solar panel to power your RFID reader module, you will need to connect it in a certain way for the pi to read the tag information. The linked solar panel has an adapter for attaching wires, we will be using this to connect the RFID reader module and the pi to the solar panel. This will not power the pi, only the thing the solar panel is powering is the RFID reader module.

- Pin \+5-9v on the reader needs to connect to the positive side of the adapter  
- GND on the reader needs to connect to the negative side of the adapter  
- Keeping the GND connected, add another wire from the negative side of the solar panel adapter to the pi  
  - This creates a full circuit for the RFID module to work. If you do not create the circuit and decide not to connect a pi GND to the solar panel the pi cannot decipher the incoming information from the RFID module.

The BME280 kit comes with its own wires, therefore extra wires are not needed for this connection. Since we are also using an RTC module, we will have to connect the BME280 to the Pi via the SPI connections, not the I2C. Not only this, but the BME needs to be set to address (ADDR switch) 0x77 to be recognized by the pi in this configuration.

- VCC on the sensor needs to connect to pin 4 on the pi (5 volt)  
- GND on the sensor needs to connect to pin 20 on the pi (ground pin closest to the SPI pins)  
- SCL/SCK on the sensor needs to connect to pin 23 on the pi (SCLK)  
- SDA/MOSI on the sensor needs to connect to pin 19 on the pi (MOSI)  
- MISO/ADDR on the sensor needs to connect to pin 21 on the pi (MISO)  
- CS on the sensor needs to connect to pin 24 on the pi (CE0)

The camera that we use comes with two ribbon cables, a 15 to 22 pin and a 22 to 22 pin. These are included so the camera can connect to all Raspberry Pis that have a camera port. Check which pi uses what cable and connect the camera to the camera port (Pi 5s and Pi 4s have two ports, use cam1 if you put \`dtoverlay=imx708\` in the config.txt file, and cam0 if you put \`dtoverlay=imx708,cam0\`)

# Testing your Pi

Congratulations\! You have fully set up your trap, but does it work? Reboot your pi and start testing. If you used a Pi 3 and disabled the GUI (recommended due to RAM usage) type \`startx\` into your terminal. This will take you to the main home screen that you are used to seeing.

Then you can check your folders for a couple of things, the folder that holds your MotionDetection\_20261022.py code should have an extra folder that was created when the camera detected something. In this folder, there should be some pictures. Wave your hand in front of the camera to see if it adds a photo. If it does, congratulations\! The motion camera is fully set up\! Now let's check the RFID module.

Go to the folder that holds your RFID\_BME\_SPI\_20261022.py. There should be another folder for that one as well, and it should be named \`RFIDpics\` (or something similar). Click on that folder. This one should not have any pictures in it due to it being RFID activated. Take a spare RFID/PIT tag and run it over your copper loop. If a picture populates the folder, then at least one part of the code is working. Back out of the picture folder and look for a .csv file that is named RFID. Click on the file and look for the time and RFID number. If its close to the current time, then you have a fully successful code\!

For the HourlyBMESPI.py it is a little different. This requires patience to check, as it runs every hour on the hour. Sit back, take a nap, write a paper, or take a walk\! When you come back to it after the hour has hit, check the folder with the HourlyBMESPI.py code. There should be a .csv file named HourlyClimateReader (or something similar). If that .csv has an entry from the last hour, then it worked\!

All your code is now working and your pi is ready to be implemented in the field. If you need to check if your Pi is working in the field, you can use a free program called cyberduck. This program lets you drop files into your Pi, as well as copy them over to your computer while on the same wifi connection. To do this easily, I use my mobile hotspot on my phone, as it tells me the I.P. address of the Pi. Once you have downloaded cyberduck and have it up and running, connect the Pi to your phone via hotspot and connect your computer to the same hotspot. Then grab the I.P. address of the Pi from your phone and input it into cyberduck. Once it connects, you should be able to see all the files that are on your Pi. From there, you can tell if the Pi is populating the files from above by navigating to those specific locations/folder/files.

# Resources/Questions

If you have any questions, comments, or concerns about the coding or physical setup of the project, please feel free to contact Harlie White at [white.harlie@gmail.com](mailto:white.harlie@gmail.com) and write in the subject line \`RFID Project: \`. I will get to your emails as soon as possible.