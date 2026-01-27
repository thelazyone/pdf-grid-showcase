@echo off
echo Building green_remover.exe...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Build the executable
pyinstaller --onefile --clean --name green_remover green_remover.py

echo.
echo Build complete!
echo The executable is in the 'dist' folder: dist\green_remover.exe
echo.
echo You can now distribute just the green_remover.exe file.
echo Users can run it like: green_remover.exe cards
pause
