#!/bin/python3
import os
import re
import subprocess
import argparse
import signal
import sys
import time
from itertools import zip_longest

import pidfile

MESSAGE_SPLIT = b'\x03'
MIDDLE_SPLIT = b'\x1e'
START_MESSAGE = b'\x1e'

COMMAND_PARSE = re.compile(b'\x02([^\x1e]+)\x1e(.*)')


reset_file = False

def handler(signum, frame):
    global reset_file
    reset_file = True
    signal.signal(signal.SIGINT, handler)

# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGUSR1, handler)

parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                 description='''
Daemon to react to power mode changes from tuxedo-keyboard driver
Program designed and only tested in Linux.
This tool will open and hang on /dev/tuxedo/user_events
If you need to reload tuxedo drivers for any reason, just send a SIGUSR1 to this program or restart the service.
This program will close the file descriptor, backoff for 5 seconds and then connect again.

The commands run by this program !!!WILL RUN AS ROOT!!! so be very careful which programs you set to run
''')


parser.add_argument('--power-command', nargs='*', default=argparse.SUPPRESS, help='''
The commands to run, if not overridden by specific power setting command
If the commands requires an argument for the power setting use {} as the placeholder
If an argument contains either the characters {} escape it by doubling. Examples:
Find the file 'thing' and use it as an argument for 'echo':
    find /home -name 'thing' -exec echo power mode {{}} \;
     
Find the file matching '{other.thing*' and run it and also use the current power mode as an argument
    find /home -name '{{other.thing*' -exec {{}} {} \; 
'''.strip()
)

parser.add_argument('--power-command-cwd', nargs='*', default='.', help='''
Default work dirs for all commands.
Important to note that the replacement must always be for all commands. 
You cannot specify some work directories here and the rest of them for the command itself
'''.strip()
)

parser.add_argument('--low-power', nargs='*', default=argparse.SUPPRESS, help='Command to run when in low power profile')
parser.add_argument('--low-power-cwd', nargs='*', default='.', help='Work dir for the command')

parser.add_argument('--medium-power', nargs='*', default=argparse.SUPPRESS, help='Command to run when in medium power profile')
parser.add_argument('--medium-power-cwd', nargs='*', default='.', help='Work dir for the command')

parser.add_argument('--high-power', nargs='*', default=argparse.SUPPRESS, help='Command to run when in high power profile')
parser.add_argument('--high-power-cwd', nargs='*', default='.', help='Work dir for the command')


class DefaultedNamespace(argparse.Namespace):

    def __getattr__(self, item):
        try:
            return self.__dict__[item]
        except KeyError as e:
            try:
                if item in ('low_power', 'medium_power', 'high_power'):
                    return self.__dict__['power_command']
                if item in ('low_power_cwd', 'medium_power_cwd', 'high_power_cwd'):
                    return self.__dict__['power_command_cwd']
            except KeyError as e:
                raise AttributeError from e
            raise AttributeError from e



args = parser.parse_args(namespace=DefaultedNamespace())


for item in ('low_power', 'medium_power', 'high_power') + ('low_power_cwd', 'medium_power_cwd', 'high_power_cwd'):
    try:
        getattr(args, item)
    except AttributeError:
        parser.error('Either --{} or --{} must be defined (others may be missing too)'
                     .format(item, 'power-command' + ('_cwd' if '_cwd' in item else '')))


def low_power():
    print("low power: {}".format(args.low_power))
    for command, cwd in zip_longest(args.low_power, args.low_power_cwd):
        if command:
            subprocess.call(command.format("0"), cwd=cwd or '.', shell=True)
        else:
            print("Too many cwd for low power mode")

def medium_power():
    print("medium power: {}".format(args.high_power))
    for command, cwd in zip_longest(args.high_power, args.high_power_cwd):
        if command:
            subprocess.call(command.format("1"), cwd=cwd, shell=True)
        else:
            print("Too many cwd for low power mode")

def high_power():
    print("high power: {}".format(args.high_power))
    for command, cwd in zip_longest(args.high_power, args.high_power_cwd):
        if command:
            subprocess.call(command.format("2"), cwd=cwd, shell=True)
        else:
            print("Too many cwd for low power mode")

POWER_SETTING_OPERATIONS = {
    0: low_power,
    1: medium_power,
    2: high_power,
}


with pidfile.PidFile('/run/' + os.path.basename(__file__)):

    while True:
        with open("/dev/tuxedo/user_events", mode="rb") as events_file:
            print(events_file)

            while True:
                accu = b''
                try:
                    read = accu + events_file.read1(50)
                except KeyboardInterrupt:
                    if reset_file:
                        break
                    raise


                if MESSAGE_SPLIT not in read:
                    accu = read
                    continue

                *splits, accu = read.split(MESSAGE_SPLIT)

                for split in splits:
                    matched = COMMAND_PARSE.search(split)

                    if matched[1] == b'P':
                        print("power-setting change to", int(matched[2]))
                        POWER_SETTING_OPERATIONS[int(matched[2])]()

                    else:
                        print("unknown command", matched[1])

        if reset_file:
            reset_file = False
            time.sleep(5)  # Wait for the driver to reload with grace time

