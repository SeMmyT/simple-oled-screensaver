# Simple oled screensaver
Hello Oled owners!

For the past few weeks of owning an OLED monitor, I've run into an issue with Windows screensaver or display-off after timeout functionality not kicking in despite everything being set as intended.

In my case, I had an issue with an active OBS replay buffer and active discord chat blocking display from sleep, which for some weird reason disables screensaver as well. You can check what program uses the screen via "powercfg /requests" command in the admin-rights command prompt.

The workaround for this is the following:



Python installation & dependencies:

Install Python:

If you don’t have Python installed, download and install it from python.org.

Make sure to check the box to "Add Python to PATH" during installation.

Open Command Prompt and install pyinstaller by running: pip install pyinstaller

Install Other Dependencies:

pip install pygetwindow psutil pynput pystray pillow pywin32 inputs

win+r shell:startup ; drop the script there.

___
Changelog 0.2
Added gamepad support, a cleaner start of the screensaver, and additional players to the list.
Please dm me on Reddit u/semmy_t if you'd like to get an .exe of this script.
