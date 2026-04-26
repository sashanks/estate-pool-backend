#!/bin/bash

# Neighborhood Due Diligence API - Quick Start Script
# This script sets up and runs the API locally

set -e

echo "🏘️  Neighborhood Due Diligence API - Quick Start"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📦 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check for .env file
echo -e "\n${YELLOW}Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please configure .env with your credentials${NC}"
    echo "   - Add Firebase credentials path"
    echo "   - Add Google API/SerpApi key (optional)"
    echo "   - Verify Ollama URL"
fi

# Check for firebase_credentials.json
if [ ! -f "firebase_credentials.json" ]; then
    echo -e "${RED}❌ firebase_credentials.json not found${NC}"
    echo "   Please download from Firebase Console and place in this directory"
    exit 1
fi
echo -e "${GREEN}✓ Firebase credentials found${NC}"

# Check Ollama
echo -e "\n${YELLOW}Checking Ollama connection...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running on localhost:11434${NC}"
else
    echo -e "${RED}⚠️  Ollama is not responding on localhost:11434${NC}"
    echo "   Make sure to run: ollama serve"
    echo "   In another terminal, verify with: ollama list"
fi

# Create cache directory
echo -e "\n${YELLOW}Setting up cache directory...${NC}"
mkdir -p cache
echo -e "${GREEN}✓ Cache directory ready${NC}"

# Ready to start
echo -e "\n${GREEN}=================================================="
echo "✅ Setup complete!"
echo "==================================================${NC}"
echo ""
echo "To start the API server, run:"
echo -e "${GREEN}python main.py${NC}"
echo ""
echo "Or with uvicorn for development:"
echo -e "${GREEN}uvicorn main:app --reload${NC}"
echo ""
echo "API Documentation:"
echo -e "${GREEN}http://localhost:8000/docs${NC}"
echo ""
