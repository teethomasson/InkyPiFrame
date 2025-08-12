#!/bin/bash
# filepath: /home/tee/InkyPiFrame/InkyPiFrame/start_inky.sh

# Active python virtual environment
source ~/.virtualenvs/pimoroni/bin/activate

# Kill any existing Python processes
pkill -f "python3 display.py"

# Kill any existing dotnet processes
pkill -f "dotnet run"

# Wait a moment for processes to clean up
sleep 2
# Change to the InkyPiFrame directory
cd /home/tee/InkyPiFrame/InkyPiFrame

# Start the InkyPiFrame application
dotnet run --project InkyPiFrame.csproj &

# Start the Python script for button handling
python3 display.py &

# Keep the script running
wait