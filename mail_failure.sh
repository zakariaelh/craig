#!/bin/bash

RECIPIENT=elhjouji.zakaria@gmail.com
LOG_FILE=$1

cat $LOG_FILE | mail -s "Your cronjob failed. See logs below!"  $RECIPIENT
