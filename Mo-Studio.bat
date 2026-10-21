@echo off
rem Bấm đúp để mở Dreamnostalgic Studio (giao diện web trên máy). Đóng cửa sổ này để tắt.
chcp 65001 >nul
cd /d "%~dp0"
python tools\web.py
pause
