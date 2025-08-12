#!/bin/bash
# filepath: /home/tee/InkyPiFrame/InkyPiFrame/start_inky.sh

# Active python virtual environment
source ~/.virtualenvs/pimoroni/bin/activate

# Change to the InkyPiFrame directory
cd /home/tee/InkyPiFrame/InkyPiFrame

# Start the InkyPiFrame application
dotnet run --project InkyPiFrame.csproj &

# Start the Python script for button handling
python3 display.py &

# Keep the script running
wait