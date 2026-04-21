#!/bin/bash

# Linux/Mac script to run the project with Docker

echo ""
echo "===================================="
echo "  Skin Cancer Detection Project"
echo "  Docker Setup Script"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed"
    echo "Please install Docker from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "[OK] Docker detected"
echo ""

# Build and start containers
echo "[*] Building and starting Docker containers..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start Docker containers"
    exit 1
fi

echo ""
echo "===================================="
echo "  Services Started Successfully!"
echo "===================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
