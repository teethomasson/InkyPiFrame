#!/bin/bash
# filepath: /home/tee/InkyPiFrame/InkyPiFrame/start_inky.sh

# Active python virtual environment
source ~/.virtualenvs/pimoroni/bin/activate

# Change to the InkyPiFrame directory
cd /home/tee/InkyPiFrame/InkyPiFrame

# Start the InkyPiFrame application
dotnet run Program.cs