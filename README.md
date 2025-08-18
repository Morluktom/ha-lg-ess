# ha-lg-ess
HomeAssistant HACS integration for the LG ESS inverter.


[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Morluktom&repository=ha-lg-ess)

If anyone would like to support me in my work, I would be happy to have a coffee.
[Buy Me a Coffee](https://www.buymeacoffee.com/qksbwfxrqkg)


## Setup

The integration can be configured easily through the UI after getting the password. It should be auto discovered, and only the password has to be entered.


### Getting the password
####  Possibility Number 1
The password is the MAC address of the LAN interface of the ESS in lower case and without :.
The MAC address can be read in the Fritzbox (or other router). (Thanks riessfa)

####  Possibility Number 2
1. Download the file [LG_Ess_Password.exe](https://github.com/Morluktom/ioBroker.lg-ess-home/tree/master/tools)
1. Connect the computer to the WLAN of the LG_ESS system. (WLAN password is on the type plate)
1. Start LG_Ess_Password.exe (At least .Net Framework 4.5 required)
1. Make a note of your password

####  Possibility Number 3
For those, who don't like exe: (Thanks grex1975)\
you can use any REST Client to get the password:
1. connect to the WLAN of the LG_ESS
1. Execute a POST request\
	Url: https://192.168.23.1/v1/user/setting/read/password \
	Headers: "Charset": "UTF-8", "Content-Type": "application/json"\
	{Body: "key": "lgepmsuser!@#"}

This should give you the password and a status in return.

## License
MIT License

Copyright (c) 2025 Morluktom <strassertom@gmx.de>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

