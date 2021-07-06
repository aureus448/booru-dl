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

***See "Config File Setup" below for information on how to configure the configuration file***

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

## Config File Setup
Note: This is a duplicate of the documentation for config.py available [here](https://aureus448.github.io/booru-dl/files/config.html).

A default configuration will be created on first run if none is provided.
A configuration file is required to have the following data sections/fields:

1. URI
    * uri: URL/URI of booru website (Ex. <https://google.com>)
    * ``OPTIONAL`` api: API key for the booru website
    * ``SEMI-OPTIONAL`` user: Username for the booru website

2. Default
    * ``OPTIONAL`` days: Default amount of days to search for
    * ``OPTIONAL`` ratings: Default rating(s) to search for
    * ``OPTIONAL`` min_score: Default minimum score for each post
    * ``OPTIONAL`` min_favs: Default minimum favorites for each post
    * ``OPTIONAL`` allowed_types: Default allowed filetypes for all sections

3. Other
    * ``OPTIONAL`` organize_by_type: Whether files should be organized by filetype in each section

        Example: For section ``Dog``, gifs will go into a ``Dog/gif`` sub-folder

4. Blacklist
    * ``OPTIONAL`` tags: list of tags to ignore

        Example: ``cat`` - what a disgusting creature

5. <Sections to Search #1 -> #n>
    If data is missing for any field other than tag, the data is collected from the
    default provided in the configuration file.

    * tags: Tags to search for the section
    * ``OPTIONAL`` days:  days to search for section
    * ``OPTIONAL`` ratings: ratings to search for section
    * ``OPTIONAL`` min_score: minimum score to search for in a section
    * ``OPTIONAL`` ignore_tags: Tags to ignore for this specific section

        Example: ``cat`` in blacklist and ignore_tags means for this specific section ``cat`` is allowed

    * ``OPTIONAL`` allowed_types: List of filetypes to allow for a specific section

Note:
Attributes that are listed as ``OPTIONAL`` mean that the code is designed to auto-fill these fields with
appropriate data where missing. Anything not listed as ``OPTIONAL`` is therefore required to prevent the code
from crashing and/or unexpected code behavior.

    For example, when data is missing for defaults, the [Default] section is set to::

        [Default]
        days = 20
        ratings = s
        min_score = 20
        min_faves = 0
        allowed_types = jpg, gif, png

    And in this vein, missing section data is set to the defaults values either provided above or in the config.

## Warning for booru-dl.exe
If you see `Trojan:Win32/Wacatac.B!ml` or `Program:Win32/Wacapew.C!ml` and are worried about booru-dl.exe, please see:
* <https://stackoverflow.com/questions/43777106/program-made-with-pyinstaller-now-seen-as-a-trojan-horse-by-avg>
* <https://stackoverflow.com/questions/54733909/windows-defender-alert-users-from-my-pyinstaller-exe>
* <https://stackoverflow.com/questions/64788656/exe-file-made-with-pyinstaller-being-reported-as-a-virus-threat-by-windows-defen>

There is no Trojan, but for some reason the Pre-installed/compiled Python bootloader (part of Python's standard library) is flagged as a virus, meaning any program that includes that bootloader (py2exe, pyinstaller, auto-py-to-exe, etc) will always be seen as a virus unless compiled from scratch. I'll consider doing this for myself.

See: [Here](https://www.virustotal.com/gui/file/d34789e7ac425b842788c2b67517181a58a4b56d84fa4c46a378db85d9f81216/detection) for VirtusTotal scan - Microsoft flags the file where any other respected anti-virus (ZoneAlarm, Bitdefender...) doesn't
