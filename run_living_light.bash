# A Linux bash script to run the Living Light program and
# store logging information to a log file
#
# To schedule this script for automatic execution via cron, see:
# https://www.dexterindustries.com/howto/auto-run-python-programs-on-the-raspberry-pi/
# 
# To configure cron to automatically start up living light, enter the command:
# sudo crontab -e
#
# and then insert the following as the last line:
# @reboot sudo /home/pi/Documents/living_light/run_living_light.bash 2&1 > /home/pi/Documents/living_light/logs/log_run_ll.txt
#
# To see the contents of the Raspberry Pi bootlog, enter the command:
# grep cron /var/log/syslog
#
# Shell command that sets a variable indicating unattended operation,
# changes directory to /home/pi/living_light, and then runs the living_light code,
# with any output messages saved to a file
#
# Command Line Arg
# * UNATTENDED: Run unattended (via cron)
#      => Keypad 1+2+3+4 stops the living light program
#      => Keypad 1, 2 or 3 sets the corresponding Scenario (Idle, Standard, Energy)
#      => Disables other Keypad commands
#
# * No args: Run interactively
#      => All keyboard commands are supported
#
# IMPT: Be sure to run "chmod +x run_living_light.bash" after any "git pull"

cd /home/pi/Documents/living_light; sudo python3 ./living_light.py UNATTENDED 2>&1
