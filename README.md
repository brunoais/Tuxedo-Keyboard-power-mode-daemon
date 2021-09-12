# Tuxedo Keyboard(-connectd) Power Mode Daemon

Execute command based on power mode set.
Requires `tuxedo-keyboard` driver

# What is

This program runs as daemon root, reacting upon a power mode changes reported by tuxedo keyboard then
runs the command associated to the power mode set.  

# What is for

1. Give real purpose to the power mode button
2. Less clicking or keyboard shortcutting to apply power changes to the PC

# How to install

1. `git clone https://github.com/brunoais/tuxedo-keyboard-power-mode-switcher.git`
2. Copy `power_events.py.run.example` as `power_events.py.run`
3. Modify `power_events.py.run` so the actions for each power mode are represented
   1. If your PC lacks a power mode, you may just type a dummy command such as an `echo """`
4. `sudo make install`

## The `power_events.py.run`

`power_events.py.run` contains the command line options to execute when calling the script.
For an explanation on the command line options, just run `python3 power_events.py`.

## Notes

1. Code must be run with root to be successful
2. `pidfile` package is installed globally during the installation process

