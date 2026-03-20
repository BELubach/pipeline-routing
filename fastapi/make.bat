@echo off
REM Helper script for common development tasks

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="db-up" goto db-up
if "%1"=="db-down" goto db-down
if "%1"=="db-reset" goto db-reset
if "%1"=="db-logs" goto db-logs
if "%1"=="migrate" goto migrate
if "%1"=="migrate-create" goto migrate-create
if "%1"=="migrate-down" goto migrate-down
if "%1"=="migrate-history" goto migrate-history
if "%1"=="run" goto run
if "%1"=="clean" goto clean

:help
echo Usage: make.bat [command]
echo.
echo Available commands:
echo   help              Show this help message
echo   install           Install dependencies
echo   db-up             Start PostgreSQL with Docker
echo   db-down           Stop PostgreSQL
echo   db-reset          Reset database (WARNING: destroys all data)
echo   db-logs           Show database logs
echo   migrate           Run database migrations
echo   migrate-create    Create new migration (use: make.bat migrate-create "description")
echo   migrate-down      Rollback last migration
echo   migrate-history   Show migration history
echo   run               Run the application
echo   clean             Clean up cache files
goto end

:install
echo Installing dependencies...
pip install -r requirements.txt
goto end

:db-up
echo Starting PostgreSQL with Docker...
docker-compose up -d
echo Waiting for database to be ready...
timeout /t 5 /nobreak >nul
goto end

:db-down
echo Stopping PostgreSQL...
docker-compose down
goto end

:db-reset
echo WARNING: This will destroy all data!
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    docker-compose down -v
    docker-compose up -d
    echo Waiting for database to be ready...
    timeout /t 5 /nobreak >nul
)
goto end

:db-logs
docker-compose logs -f postgres
goto end

:migrate
echo Running database migrations...
alembic upgrade head
goto end

:migrate-create
if "%2"=="" (
    echo Error: Migration description required
    echo Usage: make.bat migrate-create "description"
    goto end
)
echo Creating new migration: %2
alembic revision --autogenerate -m %2
goto end

:migrate-down
echo Rolling back last migration...
alembic downgrade -1
goto end

:migrate-history
alembic history
goto end

:run
echo Starting application...
uvicorn app.main:app --reload
goto end

:clean
echo Cleaning up cache files...
for /d /r %%i in (__pycache__) do @if exist "%%i" rd /s /q "%%i"
for /d /r %%i in (.pytest_cache) do @if exist "%%i" rd /s /q "%%i"
for /d /r %%i in (.mypy_cache) do @if exist "%%i" rd /s /q "%%i"
del /s /q *.pyc 2>nul
echo Done!
goto end

:end
