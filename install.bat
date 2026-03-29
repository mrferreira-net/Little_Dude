@echo off

echo ==== Little Dude Installer ====
echo Installing Python 3.7.3
echo Please follow the installation instructions and make sure to add Python to your PATH environment variable.
call .\Data\python-3.7.3.exe

echo.
echo.

echo Installing required Python packages in a virtual environment
python3 -m venv .venv
call .venv\Scripts\activate.bat
python3 -m pip install pygame-ce
python3 -m pip install numpy

echo.
echo.

echo Installation complete! You can now run the game by double clicking launch.bat
pause

