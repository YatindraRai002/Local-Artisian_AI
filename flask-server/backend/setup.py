#!/usr/bin/env python3
"""
Setup script for Kala-Kaart AI Chatbot Backend
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🚀 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"Command failed: {command}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def setup_environment():
    """Set up the Python environment and dependencies"""
    
    print("🎯 Setting up Kala-Kaart AI Chatbot Backend")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print("❌ Python 3.8+ required. Please upgrade your Python version.")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate && '
    else:  # Linux/Mac
        activate_cmd = 'source venv/bin/activate && '
    
    # Install requirements
    if not run_command(f'{activate_cmd}pip install -r requirements.txt', 
                      'Installing Python dependencies'):
        return False
    
    # Check if CSV file exists
    csv_path = Path('../src/Artisans.csv')
    if not csv_path.exists():
        print(f"⚠️  Warning: CSV file not found at {csv_path}")
        print("Please ensure the Artisans.csv file is in the correct location.")
        return False
    
    print(f"✅ CSV file found: {csv_path}")
    
    # Create .env file template
    env_path = Path('.env')
    if not env_path.exists():
        env_content = """# Kala-Kaart AI Chatbot Configuration

# OpenAI API Key (Optional - for enhanced responses)
# OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Database Configuration
CSV_PATH=../src/Artisans.csv
MODEL_DATA_PATH=model_data.pkl

# Logging
LOG_LEVEL=INFO
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env configuration file")
    
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Start the backend server:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python api.py")
    print("\n2. Start the frontend (in another terminal):")
    print("   cd ..")
    print("   npm run dev")
    print("\n3. Optional: Add your OpenAI API key to .env for enhanced responses")
    print("\n🌟 Your AI-powered artisan discovery platform is ready!")
    
    return True

def test_setup():
    """Test if the setup was successful"""
    print("\n🧪 Testing setup...")
    
    # Test imports
    try:
        import pandas as pd
        import numpy as np
        import sklearn
        import transformers
        import sentence_transformers
        print("✅ All required libraries imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    if setup_environment() and test_setup():
        print("\n🚀 Setup completed! You can now start the server.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)