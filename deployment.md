# Deployment Guide

This guide describes how to deploy the HEAC 0.2 application locally or using Docker.

## Option 1: Local Windows Deployment

The easiest way to run the application on Windows is using the provided batch script.

### Prerequisites
- Python 3.8 or higher installed and added to PATH.

### Steps
1. Navigate to the `install` directory.
2. Double-click `run_app.bat`.

The script will automatically:
- Create a virtual environment (`.venv`) if it doesn't exist.
- Install all dependencies from `requirements.txt`.
- Launch the Streamlit application in your default web browser.

## Option 2: Docker Deployment

For a platform-independent deployment, you can use Docker.

### Prerequisites
- Docker Desktop installed and running.

### Steps

#### 1. Build the Docker Image
Open a terminal in the project root directory and run:

```bash
docker build -t heac02 .
```

#### 2. Run the Container
Run the following command to start the container:

```bash
docker run -p 8501:8501 heac02
```

The application will be accessible at `http://localhost:8501`.

### Managing the Container
- To see running containers: `docker ps`
- To stop the container: `docker stop <container_id>`
