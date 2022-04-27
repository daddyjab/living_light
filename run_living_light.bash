# A Linux bash script to run the Living Light program and
# store logging information to a log file
#
# To schedule this script for automatic execution via cron, see:
# https://www.dexterindustries.com/howto/auto-run-python-programs-on-the-raspberry-pi/
#
# LL_ATTENDED values:
# * 1: Run unattended (via cron)
#   => Disables Keypad commands that require console/keyboard input
#   => Disables the Keypad 1+2+3+4 sequence (the program does not stop)
#
# * 0 or not populated: Run interactively
#   => All keyboard commands are supported
#   => Keypad 1+2+3+4 stops the living light program

export LL_UNATTENDED=1; cd /home/pi/living_light; sudo python3 ./living_light.py 2>&1 > ./logs/log_$$.txt