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

# Check if .env file exists, if not create from .env.example
echo "1. Checking environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "   Creating .env file from .env.example..."
        cp .env.example .env
        echo "   ✓ .env file created successfully!"
        echo "   ⚠️  IMPORTANT: Please review and update the .env file with your settings"
        echo "   (especially SECRET_KEY and database credentials if needed)"
        echo ""
    else
        echo "   Error: .env.example file not found!"
        exit 1
    fi
else
    echo "   ✓ .env file already exists"
    echo ""
fi

echo "2. Building Docker containers..."
docker-compose build

echo ""
echo "3. Starting services..."
docker-compose up -d

echo ""
echo "4. Waiting for database to be ready..."
sleep 10

echo ""
echo "5. Running database migrations..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "6. Collecting static files..."
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
echo "   - Main interface: http://localhost:80"
echo "   - Admin panel: http://localhost:80/admin"
echo ""
echo "To view logs:"
echo "   docker-compose logs -f web"
echo ""
echo "To stop the application:"
echo "   docker-compose down"
echo ""
