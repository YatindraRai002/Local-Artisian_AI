#!/usr/bin/env python3
"""
Quick Start Training Script for Multilingual RAG Chatbot
Simplified interface for training with optimal settings
"""

import os
import sys
import time
import glob
import logging
from sentence_transformers import SentenceTransformer
from backend.training.train_models import ComprehensiveModelTrainer
from backend import multilingual_training_data

# Use a multilingual model for all languages
embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ---------------- System Checks ---------------- #
def check_system_requirements():
    logger.info("Checking system requirements...")
    requirements = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'sentence_transformers': 'Sentence Transformers',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'sklearn': 'Scikit-learn'
    }
    missing = []
    for package, name in requirements.items():
        try:
            __import__(package)
            logger.info(f"✅ {name} - OK")
        except ImportError:
            logger.error(f"❌ {name} - MISSING")
            missing.append(package)
    if missing:
        logger.error(f"Missing packages: {', '.join(missing)}")
        logger.error("Please install missing packages with: pip install -r requirements.txt")
        return False
    return True

def check_gpu_availability():
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            gpu_name = torch.cuda.get_device_name(current_device)
            logger.info(f"🚀 GPU Available: {gpu_name} (Device {current_device}/{gpu_count})")
            return True
        else:
            logger.info("💻 GPU not available, using CPU (training will be slower)")
            return False
    except ImportError:
        logger.warning("Could not check GPU availability")
        return False

# ---------------- File Setup ---------------- #
def create_directories():
    directories = [
        'models', 'training_data', 'logs', 'trained_models',
        'chroma_db', 'vector_stores'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"📁 Created directory: {directory}")

def find_csv_file():
    possible_paths = [
        "frontend/src/Artisans.csv",
        "frontend/Artisans.csv",
        "Artisans.csv",
        "backend/Artisans.csv"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"✅ Found artist data at: {path}")
            return path
    logger.error("❌ Could not find Artisans.csv!")
    return None

# ---------------- Reusability ---------------- #
def get_latest_training_data():
    files = glob.glob("backend/training/training_data/multilingual_training_data_*.json")
    if files:
        latest_file = max(files, key=os.path.getctime)
        logger.info(f"♻️ Using existing training data: {latest_file}")
        return latest_file
    return None

def get_latest_model():
    folders = glob.glob("backend/models/rag_model_*")
    if folders:
        latest_folder = max(folders, key=os.path.getctime)
        logger.info(f"♻️ Using existing model folder: {latest_folder}")
        return latest_folder
    return None

# ---------------- Interactive Config ---------------- #
def train_models_interactive():
    print("🤖 Welcome to Kala-Kaart Multilingual RAG Chatbot Training!")
    print("=" * 60)
    
    try:
        samples = int(input("Number of training samples (default: 1000): ") or "1000")
    except ValueError:
        samples = 1000
    
    try:
        batch_size = int(input("Batch size (default: 8): ") or "8")
    except ValueError:
        batch_size = 8
    
    try:
        epochs = int(input("Training epochs (default: 3): ") or "3")
    except ValueError:
        epochs = 3
    
    use_gpu = input("Use GPU if available? (y/n, default: y): ").lower() != 'n'
    
    config = {
        'samples': samples,
        'batch_size': batch_size,
        'epochs': epochs,
        'use_gpu': use_gpu
    }
    
    print("\n🎯 Training Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    confirm = input("\nProceed with training? (y/n): ").lower()
    if confirm != 'y':
        print("Training cancelled.")
        return None
    
    return config

# ---------------- Training Pipeline ---------------- #
def run_training_pipeline(config):
    logger.info("🚀 Starting comprehensive training pipeline...")
    start_time = time.time()
    try:
        latest_model_path = get_latest_model()
        latest_data_path = get_latest_training_data()

        trainer = ComprehensiveModelTrainer({
            'batch_size': config['batch_size'],
            'intent_epochs': config['epochs'],
            'language_epochs': max(2, config['epochs'] - 1),
            'generation_epochs': max(2, config['epochs'] - 1),
            'existing_model_path': latest_model_path,
            'existing_data_path': latest_data_path
        })
        
        results = trainer.run_comprehensive_training(config['samples'])
        
        training_time = time.time() - start_time
        
        print("\n🎉" * 20)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("🎉" * 20)
        
        print(f"\n⏱️ Total Training Time: {training_time/60:.1f} minutes")
        print(f"📊 Status: {results.get('status', 'unknown')}")
        print(f"📈 Training Samples: {results.get('training_samples', 0)}")
        
        if 'classification_results' in results:
            print("\n📊 Classification Model Results:")
            for task, metrics in results['classification_results'].items():
                print(f"  📈 {task.upper()}:")
                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"    {metric}: {value:.4f}")
        
        if 'evaluation_results' in results:
            print("\n🎯 Evaluation Results:")
            for metric, value in results['evaluation_results'].items():
                if isinstance(value, (int, float)):
                    print(f"  {metric}: {value:.4f}")
        
        print(f"\n💾 Models saved in: models/")
        print(f"📁 Training data: {results.get('training_data_path', 'N/A')}")
        
        print("\n🧪 Testing trained models...")
        trainer.test_trained_models()
        
        return results
    except Exception as e:
        logger.error(f"Training failed: {e}")
        print(f"\n❌ Training failed: {e}")
        return None

# ---------------- Main ---------------- #
def main():
    print("🤖 Kala-Kaart Multilingual RAG Chatbot Trainer")
    print("=" * 50)
    
    if not check_system_requirements():
        sys.exit(1)
    
    has_gpu = check_gpu_availability()
    
    create_directories()
    
    csv_path = find_csv_file()
    if not csv_path:
        sys.exit(1)
    
    config = train_models_interactive()
    if not config:
        sys.exit(0)
    
    if not has_gpu:
        config['use_gpu'] = False
        config['batch_size'] = min(config['batch_size'], 4)
    
    print("\n🏃‍♂️ Starting training...")
    print("This may take 30-60 minutes depending on your hardware.")
    print("You can monitor progress in the training.log file.")
    
    results = run_training_pipeline(config)
    
    if results:
        print("\n✅ Training completed! Your multilingual RAG chatbot is ready.")
        print("You can now start the API server with: python api.py")
        print("\n🎯 Features of your trained chatbot:")
        print("  • Multilingual support (Hindi, English, Tamil, Telugu)")
        print("  • RAG-based intelligent responses")  
        print("  • Intent classification")
        print("  • Language detection")
        print("  • Artist search and recommendation")
        print("  • Contextual conversation memory")
    else:
        print("\n❌ Training failed. Please check logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
