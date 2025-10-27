#!/bin/bash

# Thesis Manager Setup Script
# This script helps with the initial setup of the thesis manager application

echo "==================================="
echo "Thesis Manager Setup"
echo "==================================="
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install Docker and Docker Compose first."
    exit 1
fi

echo "1. Building Docker containers..."
docker-compose build

echo ""
echo "2. Starting services..."
docker-compose up -d

echo ""
echo "3. Waiting for database to be ready..."
sleep 10

echo ""
echo "4. Running database migrations..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "5. Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Create a superuser account:"
echo "   docker-compose exec web python manage.py createsuperuser"
echo ""
echo "2. Access the application:"
echo "   - Main interface: http://localhost:8000"
echo "   - Admin panel: http://localhost:8000/admin"
echo ""
echo "To view logs:"
echo "   docker-compose logs -f web"
echo ""
echo "To stop the application:"
echo "   docker-compose down"
echo ""
