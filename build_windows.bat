@echo off
REM Builds PolyonTheGame.exe (run this on a Windows machine with Python 3.10+)
REM Result: dist\PolyonTheGame.exe

python -m pip install --upgrade pip
python -m pip install pygame pyinstaller

python -m PyInstaller --onefile --windowed --name PolyonTheGame polyon_the_game.py

echo.
echo Done! The executable is at dist\PolyonTheGame.exe
pause
