# Remote testing environment

The main goal of the project is to run IoT.js and JerryScript tests on low footprint devices such as STM32F4-Discovery reference board. Since the size of the volatile memory (SRAM) can be very limited, the testing happens remotely. This means that the main control flow (test selection, output processing) happens on the host side and just the test execution happens on the device side. The communication is established over serial port or SSH.
<br />

The following table shows the supported devices and applications:

|                                        |  IoT.js   | JerryScript |
|                :---:                   |  :---:    |    :---:    |
| STM32F4-Discovery                      | &#128504; |  &#128504;  |
| Raspberry Pi 2                         | &#128504; |  &#128504;  |
| Artik053                               | &#128504; |  &#128504;  |
<br />

In the first step, all the dependencies should be installed:  
**Note**: minimum system requirement for Ubuntu: 16.04

```sh
# Assuming you are in the remote testrunner folder.
$ bash install-deps.sh
```

### Set up STM32F4-Discovery

In case of the stm32f4-discovery devices the communication happens over the serial port. That is why a `miniusb` (flashing) and a `microusb` (serial communication) cables are needed.

#### Eliminate root permission and use permanent device ID

By default, unknown devices require root permission to use them. On UNIX systems, udev rule files help to add permissions and symbolic links to the devices. ST-Link already has a pre-defined rule file that should be copied to the udev folder. This helps to flash the device without root permission.

```sh
# Assuming you are in the remote testrunner folder.
$ sudo cp deps/stlink/etc/udev/rules.d/49-stlinkv2.rules /etc/udev/rules.d/
```

It is needed to create an other udev file for the serial communication. The rules of the file should allow the member of others (like us) to read/write the serial device without root permission. Furthermore, the board is restarted at every test, so the serial device id could change (from /dev/ttyACM0 to /dev/ttyACM1) during testing. This can be eliminated, if a symbolic link could be used to identify the device.

```sh
cat >> /etc/udev/rules.d/99-udev.rules << EOL
SUBSYSTEM=="tty", ATTRS{idVendor}=="0525", ATTRS{idProduct}=="a4a7", MODE="0666", SYMLINK+="STM32F4"
EOL
```

Sources:
  * https://github.com/texane/stlink/blob/master/doc/compiling.md#permissions-with-udev
  * http://hintshop.ludvig.co.nz/show/persistent-names-usb-serial-devices/

### Set up Raspberry Pi 2

Raspberry devices should have a UNIX based operating system, like Raspbian Jessie. Since the communication happens over `SSH`, an ssh server should be installed on the device:

```sh
# Assuming you are on the device.
pi@raspberrypi $ sudo apt-get install openssh-server
```

After that, Raspberry devices can handle ssh connections. In order to avoid the authentication every time, you should create an ssh key (on your desktop) and share the public key with the device:

```sh
# Assuming you are on the host.
user@desktop $ ssh-keygen -t rsa
user@desktop $ ssh-copy-id pi@address
```

Since Raspberry devices have much more resources than microcontrollers, it is possible to use other programs to get more precise information from the tested application (iotjs, jerry). Such a program is the Freya tool of Valgrind, that monitors the memory management and provides information about the memory usage.

### Set up ARTIK 053

In case of the ARTIK 053 devices, the communication happens over the serial port. You only need a `microusb` cable in order to test. Use udev rule files to define the appropriate permissions and symbolic link for the device (like in case of STM32F4-Discovery):

```sh
cat >> /etc/udev/rules.d/99-udev.rules << EOL
SUBSYSTEMS=="usb",ATTRS{idVendor}=="0403",ATTRS{idProduct}=="6010",SYMLINK+="ARTIK053",MODE="0666" RUN+="/sbin/modprobe ftdi_sio" RUN+="/bin/sh -c 'echo 0403 6010 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id'"
EOL
```

Source:
  * https://github.com/Samsung/TizenRT/blob/master/build/configs/artik053/README.md#add-usb-device-rules



### Start testrunner

On the host side, it is enough to run the `driver.py` file.

```sh
# Assuming you are in the remote testrunner folder.
$ python driver.py
```

### Testrunner parameters:

```sh
--app
  Defines the application to test {iotjs, jerryscript}.

--app-path
  Defines the path to the application project.

--buildtype
  Defines the buildtype for the projects {release, debug}. Just for debugging.

--device
  Defines the target device {stm32f4dis, rpi2, artik053}.

--public
  Publish the test results to the public database.
  This option requires a username and a password pairs that the contributors maintain.
  These information should be set by environment variables:

  $ export FIREBASE_USER="your_user_email"
  $ export FIREBASE_PWD="your_user_password"

--timeout
  Defines a time (in seconds) when to restart the device.

--no-build
  Do not build the projects.

--no-profile-build
  Do not build the different profiles.

--no-flash
  Do not flash the device.

--no-test
  Do not test.

SSH communication:

--username
  Defines the username for the Raspberry Pi target.

--address
  IP(v4) address of the device.

--remote-workdir
  Defines the working direcory where the testing happens.

Serial communication:

--port
  Defines the serial device id (e.g. /dev/ttyACM0)

--baud
  Defines the baud rate (default: 115200)
```

### Examples to run tests

```
$ python driver.py --device stm32f4dis --app iotjs --port /dev/STM32F4 --baud 115200
$ python driver.py --device stm32f4dis --app jerryscript --port /dev/STM32F4 --baud 115200
$ python driver.py --device rpi2 --app iotjs --address a.b.c.d --username pi --remote-workdir /home/pi/testrunner
$ python driver.py --device rpi2 --app jerryscript --address a.b.c.d --username pi --remote-workdir /home/pi/testrunner
$ python driver.py --device artik053 --app iotjs --port /dev/ARTIK053 --baud 115200
$ python driver.py --device artik053 --app jerryscript --port /dev/ARTIK053 --baud 115200
```

All the results are written into JSON files that are found in a `results` folder. Name of the output files are datetime with the following format:

```
%YY-%mm-%ddT%HH.%MM.%SSZ.json      e.g. 2017-04-15T10.02.33Z.json
```

Every JSON file contain information about the test results (status, output, memory usage), environments (used hashes, commit messages) and the main section sizes of the application (iotjs or jerryscript) binary. These sizes are based on a stripped release, rpi2 build.