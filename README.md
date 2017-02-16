# IoT.js remote testing environment for microcontrollers

The main goal of the project is to run IoT.js regression test on low footprint devices such as stm32f4-discovery reference board. Since the size of the volatile memory (SRAM) can be very limited, the testing happens remotely. This means that the main control flow (test selection, output processing) happens on the host side and just the test execution happens on the device side. The communication is established via tty or telnet.

**Note: currently just the stm32f4-discovery board is supported with telnet.**

## Follow the next steps to test on a board:

#### 1. Install dependencies
```
$ bash install-deps.sh
```

#### 2. Modify the prepared NuttX configuration file

Since the testing happens via Telnet, there is a prepared NuttX configuration file in the `config` folder (netnsh.config). In this file, the internet settings part should be modified. Both CONFIG_NSH_IPADDR and CONFIG_NSH_NETMASK must be defined (in hexadecimal format like the CONFIG_NSH_DRIPADDR).

```
#
# IPv4 Addresses
#
CONFIG_NSH_IPADDR=YOUR_STATIC_IP
CONFIG_NSH_DRIPADDR=0x0a060bfe
CONFIG_NSH_NETMASK=YOUR_NETMASK
# CONFIG_NSH_DNS is not set
CONFIG_NSH_NOMAC=y
CONFIG_NSH_SWMAC=y
CONFIG_NSH_MACADDR=0x00e0deadbeef
CONFIG_NSH_MAX_ROUNDTRIP=20
```
#### 3. Initialize submodules
```
$ git submodule update --init
```

#### 4. Start testrunner
```
$ python testrunner.py
```
or
```
$ python testscheduler.py
```

Note: `testrunner.py` is just for one time testing, `testscheduler.py` is for testing every day automatically. If error happens during testing or building, a `failure.log` file contains the output of the last command.

#### Testrunner parameters:

```
--device-ip        ip address of the device
--timeout          restart the device if no response within a given time (in seconds)
--skip-init        skip building the basic environments
--public           pusblish results to the web
```

All the results are written into JSON files that are found in the `results` folder. Name of the output files are datetime with the following format:

```
%YY-%mm-%ddT%HH.%MM.%SSZ.json      e.g. 2017-04-15T10.02.33Z.json
```

Every JSON file contain information about the test results (status, output), submodules (current hash, commit messgae) and the main section sizes of the IoT.js (stripped release, RPI2 target) binary. There is a main `index.json` file that contains the names of the all available result files. It can be useful, if you want to use a webpage to show the testresults.
