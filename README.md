# booru-dl
[![codecov](https://codecov.io/gh/aureus448/booru-dl/branch/main/graph/badge.svg?token=96GB8WDQO6)](https://codecov.io/gh/aureus448/booru-dl)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Framework Status](https://github.com/aureus448/booru-dl/actions/workflows/check_code.yml/badge.svg)](https://github.com/aureus448/booru-dl/actions/workflows/check_code.yml)
[![Codebase Linter Status](https://github.com/aureus448/booru-dl/actions/workflows/check_everything.yml/badge.svg)](https://github.com/aureus448/booru-dl/actions/workflows/check_everything.yml)
[![Documentation Build](https://github.com/aureus448/booru-dl/actions/workflows/build-pages.yml/badge.svg)](https://github.com/aureus448/booru-dl/actions/workflows/build-pages.yml)

A program designed to take a given user config and collect all images from a given booru site.

For code documentation, see the [booru-dl Documentation](https://aureus448.github.io/booru-dl/).

## How to Use
This program auto-guides the user through the process of setting up the Downloader. On first run of the program, the software will automatically create a configuration file that the user will need to set up in order for the program to run. Upon setting up the configuration file, the program will begin the process of downloading files from the booru URL provided (if supported by the booru itself).

### Python
* Run `git clone https://github.com/aureus448/booru-dl.git && git checkout tags/v1.0`
    * Slight note: If running via Windows Powershell, run `git clone https://github.com/aureus448/booru-dl.git; git checkout tags/v1.0`
* Run `cd booru-dl`
* Create a virtual environment for Python if desired - steps not provided [`python -m venv venv` ***Use if you understand what this does***]
* Run `pip install -r requirements.txt`
* Run `$env:PYTHONPATH = "<path_to_repo>\booru-dl"` [Windows Powershell only]
* Run `python booru_dl/main.py`
* Upon first launch, the program will notify of need of `config.ini` data - Fill out the file (Instructions are provided within the file)
* Launch the program again with the filled out `config.ini` - The program will collect all requested data and finish execution
  ![Example Shell](https://user-images.githubusercontent.com/32879417/123506449-251b3a80-d619-11eb-9722-230a46529697.png)
  Example use of `booru-dl` repository source through PowerShell

### Executable (Highly, Highly recommended)
* Launch file `booru-dl.exe`
* Upon first launch, the program will notify of need of `config.ini` data - Fill out the file (Instructions are provided within the file)
* Launch the program again with the filled out `config.ini` - The program will collect all requested data and finish execution
  ![Example Run](https://user-images.githubusercontent.com/32879417/123506578-bbe7f700-d619-11eb-91d1-a9b4d1365650.png)
  Example use of `booru-dl.exe`

## Warning for booru-dl.exe:
If you see `Trojan:Win32/Wacatac.B!ml` or `Program:Win32/Wacapew.C!ml` and are worried about booru-dl.exe, please see:
* https://stackoverflow.com/questions/43777106/program-made-with-pyinstaller-now-seen-as-a-trojan-horse-by-avg
* https://stackoverflow.com/questions/54733909/windows-defender-alert-users-from-my-pyinstaller-exe
* https://stackoverflow.com/questions/64788656/exe-file-made-with-pyinstaller-being-reported-as-a-virus-threat-by-windows-defen

There is no Trojan, but for some reason the Pre-installed/compiled Python bootloader (part of Python's standard library) is flagged as a virus, meaning any program that includes that bootloader (py2exe, pyinstaller, auto-py-to-exe, etc) will always be seen as a virus unless compiled from scratch. I'll consider doing this for myself.

See: [Here](https://www.virustotal.com/gui/file/d34789e7ac425b842788c2b67517181a58a4b56d84fa4c46a378db85d9f81216/detection) for VirtusTotal scan - Microsoft flags the file where any other respected anti-virus (ZoneAlarm, Bitdefender...) doesn't

#### Tested with e926 as API endpoint - other boorus will likely not work (yet)
