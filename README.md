# Remote testing environment

The main goal of the project is to run IoT.js and JerryScript tests on low footprint devices such as STM32F4-Discovery reference board. Since the size of the volatile memory (SRAM) can be very limited, the testing happens remotely. This means that the main control flow (test selection, output processing) happens on the host side and just the test execution happens on the device side. The communication is established over `serial port` or `SSH`.
<br />

The following table shows the supported devices and applications:

|                                        |  IoT.js   | JerryScript |
|                :---:                   |  :---:    |    :---:    |
| STM32F4-Discovery                      | &#128504; |  &#128504;  |
| Raspberry Pi 2                         | &#128504; |  &#128504;  |
| Artik053                               | &#128504; |  &#128504;  |
<br />

In the first step, all the dependencies should be installed:

(Note: Ubuntu 14.04 LTS is not supported, please use 16.04 LTS)

```
# Install missing packages
$ bash install-deps.sh

# Download subprojects
$ bash init.sh
```
<br />

### Set up STM32F4-Discovery board to test

In case of the stm32f4-discovery devices the communication happens over the serial port. That is why a `miniusb` (flashing) and a `microusb` (serial communication) cables are needed. There are prepared NuttX configuration files in the `config` folder that contain all the settings that is required.

#### Flash the device without root permission

In order to flash the binary onto the board without the system requires root permission, copy the `49-stlinkv2.rules` to `/etc/udev/rules.d/`.

```
$ sudo cp projects/stlink/etc/udev/rules.d/49-stlinkv2.rules /etc/udev/rules.d/
```

(Source: https://github.com/texane/stlink/blob/master/doc/compiling.md#permissions-with-udev)

#### Read/write serial without root permission

Since the board is restarted at every test, the serial device id could change (from `/dev/ttyACM0` to `/dev/ttyACM1`) during testing. To eliminate this side effect, a permanent serial id should be created for the device:

http://hintshop.ludvig.co.nz/show/persistent-names-usb-serial-devices/

You need to complete the previously created udev rule with `MODE="0666"` to allow the member of others (like us) to read/write the serial device without root permission, because it is required normally.

So your udev ruleset should look like this:
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="<your vendor id>", ATTRS{idProduct}=="<your product id>", MODE="0666", SYMLINK+="STM32F4"
```

Now you can refer to the device as `/dev/STM32F4`.

<br />

### Set up Raspberry Pi 2 to test

Raspberry devices should have a UNIX based operating system, like Raspbian Jessie. Since the communication happens over `SSH`, an ssh server should be installed on the device:

```
pi@raspberrypi $ sudo apt-get install openssh-server
```

After that, Raspberry devices can handle ssh connections. In order to avoid the authentication every time, you should create an ssh key (on your desktop) and share the public key with the device:

```
user@desktop $ ssh-keygen -t rsa
user@desktop $ ssh-copy-id pi@address
```

Since Raspberry devices have much more resources than microcontrollers, it is possible to use other programs to get more precise information from the tested application (iotjs, jerry). Such a program is the Freya tool of Valgrind, that monitors the memory management and provides information about the memory usage.

<br />

### Set up Artik053 board to test

In case of the artik053 devices, the communication happens over the serial port. You only need a `microusb` cable in order to test. To handle the device without root permission, please follow the `STM32F4-Discovery` [flash](#flash-the-device-without-root-permission) and [read/write](#readwrite-serial-without-root-permission) sections.

<br />

### Start testrunner

On the host side, it is enough to run the `driver.py` file.

```
$ python driver.py
```

### Testrunner parameters:

```
--app
  Defines the application to test {iotjs, jerryscript}.

--branch
  Defines the application branch that should be tested.

--buildtype
  Defines the buildtype for the projects {release, debug}. Just for debugging.

--commit
  Defines the application commit that should be tested.

--device
  Defines the target device {stm32f4dis, rpi2, artik053}.

--public
  Publish the test results to the web projects.
  https://samsung.github.io/iotjs-test-results/
  https://jerryscript-project.github.io/jerryscript-test-results/
  Set the required environment variables (FIREBASE_USER, FIREBASE_PWD).
  ```
  $ export FIREBASE_USER="your_user_email"
  $ export FIREBASE_PWD="your_user_password"
  ```

--remote-path
  When the operating system is provided (e.g. in case of Raspberry),
  you should define, which folder contains the helper scripts to test.

--timeout
  Defines a time (in seconds) when to restart the device.

SSH communication:

--username
  Defines the username for the Raspberry Pi target.

--address
  IP(v4) address of the device.

Serial communication:

--port
  Defines the serial device id (e.g. /dev/ttyACM0)

--baud
  Defines the baud rate (default: 115200)
```

### Examples to run tests

```
$ python driver.py --device stm32f4dis --app iotjs --port /dev/ttyACM0 --baud 115200
$ python driver.py --device stm32f4dis --app jerryscript --port /dev/ttyACM0 --baud 115200
$ python driver.py --device rpi2 --app iotjs --address a.b.c.d --username pi --remote-path /home/pi/testrunner
$ python driver.py --device rpi2 --app jerryscript --address a.b.c.d --username pi --remote-path /home/pi/testrunner
$ python driver.py --device artik053 --app iotjs --port /dev/ttyUSB1 --baud 115200
$ python driver.py --device artik053 --app jerryscript --port /dev/ttyUSB1 --baud 115200
```

All the results are written into JSON files that are found in a `results` folder. Name of the output files are datetime with the following format:

```
%YY-%mm-%ddT%HH.%MM.%SSZ.json      e.g. 2017-04-15T10.02.33Z.json
```

Every JSON file contain information about the test results (status, output, memory usage), environments (used hashes, commit messages) and the main section sizes of the application (iotjs or jerryscript) binary. These sizes are based on a stripped release, rpi2 build.
