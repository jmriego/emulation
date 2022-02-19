# Launchbox2AEL

This is a program that takes your Launchbox library and exports it to Advanced Emulator Launcher so you can enjoy your library in Kodi.

# How to use Launchbox2AEL

- Install Python
- Clone this repo or download it as a zip and unzip it somewhere
- You need to go to Advance Emulator Launcher and click on Utilities -> Check/Update all databases if not already done
- Copy the config.ini.example into config.ini and modify it:
  * You need to tell it where AEL plugin is installed. It's probably one of the two options already in the example file. Leave only one line uncommented
  * Tell it where Launchbox is installed
  * dosbox exe and args are the command line parameters for running DOSBOX games
- You need to install the lxml and untangle libraries: *pip install lxml untangle*
- Run or double click Launchbox2AEL.py every time you want to export changes in your Launchbox library to AEL
