# Remote testing environment

The main goal of the project is to run IoT.js and JerryScript tests on low footprint devices such as STM32F4-Discovery reference board. Since the size of the volatile memory (SRAM) can be very limited, the testing happens remotely. This means that the main control flow (test selection, output processing) happens on the host side and just the test execution happens on the device side. The communication is established via Internet (by Telnet or SSH).

The following table shows the supported devices and applications:

|                                        |  IoT.js   | JerryScript |
|                :---:                   |  :---:    |    :---:    |
| STM32F4-Discovery                      | &#128504; |  &#128504;  |
| Raspberry Pi 2                         | &#128504; |  &#128504;  |

In general, you should install dependencies and initialize the projects before the testing:

```
$ bash install-deps.sh
$ bash init.sh
```

#### Set up STM32F4-Discovery board to test

The currently supported operating system (for testing on STM32F4) is just the NuttX. There are prepared NuttX configuration files for both **IoT.js** and **JerryScript** in the `config` folder. Since the IP address and the netmask are depend on your network infrastructure, there is an `etherrnet.config` file, where you can define these values.


The following config just shows the content of the ethernet.config:

```
+[Ethernet]
+# IPv4 address
+IP_ADDR=xxx.xxx.xxx.xxx
+NETMASK=yyy.yyy.yyy.yyy

```

Note: to ensure internet connection to the device, you should use a [base board](http://www.st.com/en/evaluation-tools/stm32f4dis-ext.html) that has ethernet port.


#### Set up Rapsberry Pi to test

First of all, you should have an operating system on the Raspberry device. It is recommend to use UNIX based system like Raspbian Jessie. After that, you should install an ssh server (on the device):

```
sudo apt-get install openssh-server
```

**Note:** add your SSH key to the Raspberry Pi 2 known host file to avoid getting password.

```
ssh-keygen -t rsa
ssh-copy-id pi@address
```

On the Raspberry Pi target, the testing mechanism is a bit different like on microcontrollers. The base concept is the same, so everything happens remotely, but there are more tools and scripts that help to run tests on the device. These tools are provided in the `resource` folder. There is an `iotjs-freya.config` file, that should be updated with your glibc version:

```
cd resources
GLIBC_VERSION=`ldd --version | awk '/ldd/{print $NF}'`
sed -ie s/2\.23/$GLIBC_VERSION/g iotjs-freya.config
```

After that, you should move the contents of the `resource` folder to the Raspberry, and run the `init-pi.sh` to build the dependencies:

```
$ ssh pi@address
pi@address ~ $ mkdir testrunner
pi@address ~ $ exit
$ scp -r resources/* pi@address:~/testrunner
$ ssh pi@address
pi@address ~ $ cd testrunner
pi@address ~ $ bash init-pi.sh
```

#### Start testrunner

On the host side, it is enough to run the `driver.py` file.

```
$ python driver.py
```

#### Testrunner parameters:

```
--address
  IP(v4) address of the device.

--app
  Defines the application to test {iotjs, jerryscript}.

--branch
  Defines the application branch that should be tested.

--buildtype
  Defines the buildtype for the application and the operating
  system {release, debug}. Just for debugging on stm32f4dis-nuttx.

--commit
  Defines the application commit that should be tested.

--device
  Defines the target device {stm32f4dis, rpi2, fake}. The fake device is
  a dummy device that can be useful when developing the test system and
  no real device available.

--public
  Publish the test results to the web projects.
  https://samsung.github.io/iotjs-test-results/
  https://jerryscript-project.github.io/jerryscript-test-results/

--timeout
  Defines a time (in seconds) when to restart the device.

--username
  Defines the username for the Raspberry Pi target.

--remote-path
  When the operating system is provided (e.g. in case of Raspberry),
  you should define, which folder contains the helper scripts to test.
```

#### Examples to run tests

```
$ python driver.py --device stm32f4dis --app iotjs --address a.b.c.d
$ python driver.py --device stm32f4dis --app jerryscript --address a.b.c.d
$ python driver.py --device rpi2 --app iotjs --address a.b.c.d --username pi --remote-path /home/pi/testrunner
$ python driver.py --device rpi2 --app jerryscript --address a.b.c.d --username pi --remote-path /home/pi/testrunner
```

All the results are written into JSON files that are found in a `results` folder. Name of the output files are datetime with the following format:

```
%YY-%mm-%ddT%HH.%MM.%SSZ.json      e.g. 2017-04-15T10.02.33Z.json
```

Every JSON file contain information about the test results (status, output, memory usage), environments (used hashes, commit messages) and the main section sizes of the application (iotjs or jerryscript) binary. These sizes are always got from a stripped release, rpi2 build.
There is a main `index.json` file that contains the names of the all available result files. It can be useful, if you want to use a webpage to show the testresults.
