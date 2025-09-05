#!/usr/bin/env python3
"""
Comprehensive Model Training Script for Multilingual RAG Chatbot
Trains all components: Intent Classification, Language Detection, and RAG models
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

# Import our custom modules
from backend.multilingual_training_data import MultilingualTrainingDataGenerator
from backend.rag_nlp_model import MultilingualRAGModel
from backend.multilingual_trainer import MultilingualTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveModelTrainer:
    """Orchestrates training of all model components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directories
        os.makedirs('models', exist_ok=True)
        os.makedirs('training_data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
    def generate_training_data(self, num_samples: int = 2000) -> str:
        """Generate multilingual training data"""
        logger.info(f"Generating {num_samples} training samples...")
        
        generator = MultilingualTrainingDataGenerator()
        
        # Generate conversations
        conversations = generator.generate_training_conversations(num_samples)
        
        # Generate knowledge base
        knowledge_base = generator.generate_craft_knowledge_base()
        
        # Save training data
        filename = f'training_data/multilingual_training_data_{self.timestamp}.json'
        generator.save_training_data(conversations, knowledge_base, filename)
        
        logger.info(f"Training data saved to {filename}")
        return filename
    
    def train_rag_model(self, training_data_path: str) -> str:
        """Train RAG model"""
        logger.info("Training RAG model...")
        
        # Initialize RAG model
        rag_model = MultilingualRAGModel()
        
        # Train from conversations
        rag_model.train_from_conversations(training_data_path)
        
        # Save trained model
        model_path = f'models/rag_model_{self.timestamp}'
        rag_model.save_model(model_path)
        
        logger.info(f"RAG model saved to {model_path}")
        return model_path
    
    def train_classification_models(self, training_data_path: str) -> Dict[str, Any]:
        """Train intent and language classification models"""
        logger.info("Training classification models...")
        
        # Training configuration
        training_config = {
            'base_model': 'bert-base-multilingual-cased',
            'batch_size': self.config.get('batch_size', 16),
            'intent_epochs': self.config.get('intent_epochs', 5),
            'language_epochs': self.config.get('language_epochs', 3),
            'generation_epochs': self.config.get('generation_epochs', 3),
            'learning_rate': 5e-5,
            'max_length': 512,
            'warmup_steps': 500,
            'weight_decay': 0.01
        }
        
        # Initialize trainer
        trainer = MultilingualTrainer(training_config)
        
        # Train full pipeline
        results = trainer.train_full_pipeline(training_data_path)
        
        logger.info("Classification models training completed")
        return results
    
    def evaluate_models(self, training_data_path: str, model_paths: Dict[str, str]) -> Dict[str, float]:
        """Evaluate trained models"""
        logger.info("Evaluating trained models...")
        
        evaluation_results = {}
        
        try:
            # Initialize trainer for evaluation
            training_config = {
                'base_model': 'bert-base-multilingual-cased',
                'batch_size': 8
            }
            trainer = MultilingualTrainer(training_config)
            
            # Evaluate models
            eval_results = trainer.evaluate_model(training_data_path)
            evaluation_results.update(eval_results)
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            evaluation_results = {'evaluation_error': str(e)}
        
        return evaluation_results
    
    def run_comprehensive_training(self, num_samples: int = 2000) -> Dict[str, Any]:
        """Run complete training pipeline"""
        logger.info("Starting comprehensive training pipeline...")
        
        results = {
            'timestamp': self.timestamp,
            'config': self.config,
            'training_samples': num_samples
        }
        
        try:
            # Step 1: Generate training data
            training_data_path = self.generate_training_data(num_samples)
            results['training_data_path'] = training_data_path
            
            # Step 2: Train RAG model
            rag_model_path = self.train_rag_model(training_data_path)
            results['rag_model_path'] = rag_model_path
            
            # Step 3: Train classification models
            classification_results = self.train_classification_models(training_data_path)
            results['classification_results'] = classification_results
            
            # Step 4: Evaluate models
            model_paths = {
                'rag_model': rag_model_path,
                'classification_models': './trained_models/'
            }
            evaluation_results = self.evaluate_models(training_data_path, model_paths)
            results['evaluation_results'] = evaluation_results
            
            # Step 5: Save final results
            self.save_training_summary(results)
            
            logger.info("Comprehensive training completed successfully!")
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            results['error'] = str(e)
            results['status'] = 'failed'
        else:
            results['status'] = 'completed'
        
        return results
    
    def save_training_summary(self, results: Dict[str, Any]):
        """Save training summary"""
        import json
        
        summary_path = f'models/training_summary_{self.timestamp}.json'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Training summary saved to {summary_path}")
        
        # Also create a latest summary link
        latest_path = 'models/latest_training_summary.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def test_trained_models(self):
        """Test trained models with sample queries"""
        logger.info("Testing trained models...")
        
        try:
            # Load RAG model
            latest_rag_path = max(
                [d for d in os.listdir('models') if d.startswith('rag_model_')],
                key=lambda x: x.split('_')[-1]
            )
            
            rag_model = MultilingualRAGModel()
            rag_model.load_model(f'models/{latest_rag_path}')
            
            # Test queries in different languages
            test_queries = [
                ("Find pottery artists in Maharashtra", "english"),
                ("मुझे राजस्थान में कलाकार चाहिए", "hindi"),
                ("तमिल नाडु में बुनकर दिखाओ", "hindi"),
                ("మట్టి కుండల తయారీదారులను చూపించండి", "telugu"),
                ("வணக்கम், நெசவு கலைஞர்களைக் காட்டுங்கள்", "tamil")
            ]
            
            logger.info("Sample test results:")
            for query, expected_lang in test_queries:
                try:
                    result = rag_model.query(query)
                    logger.info(f"Query: {query}")
                    logger.info(f"Detected Language: {result.get('detected_language', 'unknown')}")
                    logger.info(f"Response: {result.get('response', 'No response')[:100]}...")
                    logger.info("-" * 50)
                except Exception as e:
                    logger.error(f"Test query failed: {e}")
            
        except Exception as e:
            logger.error(f"Model testing failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='Train Multilingual RAG Chatbot Models')
    parser.add_argument('--samples', type=int, default=2000, help='Number of training samples to generate')
    parser.add_argument('--batch-size', type=int, default=16, help='Training batch size')
    parser.add_argument('--epochs', type=int, default=5, help='Number of training epochs')
    parser.add_argument('--test-only', action='store_true', help='Only test existing models')
    parser.add_argument('--generate-data-only', action='store_true', help='Only generate training data')
    
    args = parser.parse_args()
    
    # Training configuration
    config = {
        'batch_size': args.batch_size,
        'intent_epochs': args.epochs,
        'language_epochs': max(3, args.epochs - 2),
        'generation_epochs': max(2, args.epochs - 3),
        'num_samples': args.samples
    }
    
    # Initialize trainer
    trainer = ComprehensiveModelTrainer(config)
    
    if args.test_only:
        # Only test existing models
        trainer.test_trained_models()
        
    elif args.generate_data_only:
        # Only generate training data
        trainer.generate_training_data(args.samples)
        
    else:
        # Run full training pipeline
        results = trainer.run_comprehensive_training(args.samples)
        
        print("\n" + "="*60)
        print("TRAINING COMPLETED")
        print("="*60)
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Timestamp: {results.get('timestamp', 'unknown')}")
        print(f"Training Samples: {results.get('training_samples', 0)}")
        
        if 'classification_results' in results:
            print("\nClassification Results:")
            for task, metrics in results['classification_results'].items():
                print(f"  {task}:")
                for metric, value in metrics.items():
                    print(f"    {metric}: {value:.4f}")
        
        if 'evaluation_results' in results:
            print("\nEvaluation Results:")
            for metric, value in results['evaluation_results'].items():
                print(f"  {metric}: {value:.4f}")
        
        print(f"\nModels saved in: models/")
        print(f"Training data: {results.get('training_data_path', 'N/A')}")
        print("="*60)
        
        # Test the trained models
        trainer.test_trained_models()

if __name__ == "__main__":
    main()