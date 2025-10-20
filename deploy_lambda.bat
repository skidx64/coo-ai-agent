@echo off
REM Windows batch script for Lambda deployment

echo Starting Lambda deployment...

REM Clean up previous builds
if exist lambda-package rmdir /s /q lambda-package
if exist coo-lambda.zip del coo-lambda.zip

REM Create deployment package
echo Creating deployment package...
mkdir lambda-package
cd lambda-package

REM Install dependencies
echo Installing Lambda dependencies for Linux (this may take 2-3 minutes)...
pip install -r ..\requirements-lambda.txt -t . --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: --upgrade --quiet

REM Copy source code
echo Copying source code...
xcopy /E /I /Q ..\src src
xcopy /E /I /Q ..\frontend frontend
xcopy /E /I /Q ..\knowledge-base knowledge-base

REM Copy vector database if it exists
if exist ..\vector_db (
    echo Copying vector database...
    xcopy /E /I /Q ..\vector_db vector_db
) else (
    echo No vector_db found - RAG will use empty database
)

REM Create zip file
echo Creating zip file...
powershell Compress-Archive -Path * -DestinationPath ..\coo-lambda.zip -Force

cd ..

echo Deployment package created: coo-lambda.zip

echo.
echo Next steps:
echo 1. Go to AWS Lambda Console
echo 2. Find function: coo-api-handler
echo 3. Upload coo-lambda.zip
echo 4. Wait for upload to complete
echo 5. Test your deployment!
echo.
echo Deployment guide: BUDGET_AWS_DEPLOYMENT.md
pause
