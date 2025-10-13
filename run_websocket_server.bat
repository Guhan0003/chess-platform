@echo off
echo Starting Chess Platform with WebSocket support...
echo.
echo ===============================================
echo   Chess Platform WebSocket Server
echo   URL: http://127.0.0.1:8000
echo   WebSocket support: ENABLED
echo ===============================================
echo.
echo Press Ctrl+C to stop the server
echo.

python -m daphne -b 127.0.0.1 -p 8000 chess_backend.asgi:application