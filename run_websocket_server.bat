@echo off
setlocal
set "PYTHONWARNINGS=ignore:pkg_resources is deprecated as an API:UserWarning"
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

if not exist "testing_logs\server" mkdir "testing_logs\server"

python -m daphne -b 127.0.0.1 -p 8000 --access-log "testing_logs/server/daphne_access.log" chess_backend.asgi:application