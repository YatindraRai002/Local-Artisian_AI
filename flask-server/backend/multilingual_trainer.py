"""
Advanced Multilingual Training Pipeline for Kala-Kaart RAG Chatbot
Implements comprehensive training with custom datasets and fine-tuning
"""

import os
import json
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import (
    Trainer, TrainingArguments, 
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    BertForSequenceClassification, BertTokenizer,
    get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import pandas as pd
from typing import List, Dict, Any, Tuple
import logging
from tqdm import tqdm
import wandb
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultilingualChatbotDataset(Dataset):
    """Dataset class for multilingual chatbot training"""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 512):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Intent to ID mapping
        self.intent_to_id = {
            'greeting': 0, 'craft_search': 1, 'location_search': 2, 
            'artist_search': 3, 'help_request': 4, 'contact_info': 5,
            'statistics': 6, 'general_query': 7
        }
        
        # Language to ID mapping  
        self.lang_to_id = {
            'english': 0, 'hindi': 1, 'tamil': 2, 'telugu': 3
        }
    
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        conv = self.conversations[idx]
        
        # Prepare input text
        user_message = conv['user_message']
        bot_response = conv['bot_response']
        
        # Create input-output pairs
        input_text = f"[USER] {user_message} [BOT]"
        target_text = bot_response
        
        # Tokenize
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        target_encoding = self.tokenizer(
            target_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': input_encoding['input_ids'].flatten(),
            'attention_mask': input_encoding['attention_mask'].flatten(),
            'labels': target_encoding['input_ids'].flatten(),
            'intent_label': self.intent_to_id.get(conv['intent'], 0),
            'language_label': self.lang_to_id.get(conv['language'], 0),
            'language': conv['language'],
            'intent': conv['intent']
        }

class IntentClassificationDataset(Dataset):
    """Dataset for intent classification training"""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 256):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Create intent mapping
        intents = list(set([conv['intent'] for conv in conversations]))
        self.intent_to_id = {intent: idx for idx, intent in enumerate(intents)}
        self.id_to_intent = {idx: intent for intent, idx in self.intent_to_id.items()}
        
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        conv = self.conversations[idx]
        
        encoding = self.tokenizer(
            conv['user_message'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.intent_to_id[conv['intent']], dtype=torch.long),
            'language': conv['language']
        }

class LanguageDetectionDataset(Dataset):
    """Dataset for language detection training"""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 256):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Language mapping
        self.lang_to_id = {
            'english': 0, 'hindi': 1, 'tamil': 2, 'telugu': 3
        }
        
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        conv = self.conversations[idx]
        
        encoding = self.tokenizer(
            conv['user_message'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.lang_to_id[conv['language']], dtype=torch.long)
        }

class MultilingualTrainer:
    """Advanced trainer for multilingual chatbot models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize tokenizers and models
        self.tokenizer = AutoTokenizer.from_pretrained(
            config.get('base_model', 'bert-base-multilingual-cased')
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Initialize models
        self.intent_model = None
        self.language_model = None
        self.response_model = None
        
        # Training metrics
        self.training_history = {
            'intent_classification': [],
            'language_detection': [],
            'response_generation': []
        }
        
    def prepare_training_data(self, training_data_path: str) -> Dict[str, List]:
        """Prepare training data from JSON file"""
        logger.info(f"Loading training data from {training_data_path}")
        
        with open(training_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conversations = data['conversations']
        
        # Split by task
        train_conversations, val_conversations = train_test_split(
            conversations, test_size=0.2, random_state=42, 
            stratify=[conv['language'] for conv in conversations]
        )
        
        return {
            'train': train_conversations,
            'validation': val_conversations,
            'knowledge_base': data.get('knowledge_base', {})
        }
    
    def train_intent_classifier(self, train_data: List[Dict], val_data: List[Dict]) -> Dict[str, float]:
        """Train intent classification model"""
        logger.info("Training intent classification model...")
        
        # Create datasets
        train_dataset = IntentClassificationDataset(train_data, self.tokenizer)
        val_dataset = IntentClassificationDataset(val_data, self.tokenizer)
        
        # Initialize model
        num_labels = len(train_dataset.intent_to_id)
        self.intent_model = AutoModelForSequenceClassification.from_pretrained(
            self.config.get('base_model', 'bert-base-multilingual-cased'),
            num_labels=num_labels
        ).to(self.device)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir='./intent_classifier',
            num_train_epochs=self.config.get('intent_epochs', 3),
            per_device_train_batch_size=self.config.get('batch_size', 16),
            per_device_eval_batch_size=self.config.get('batch_size', 16),
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=100,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_f1",
            greater_is_better=True,
        )
        
        # Custom trainer with metrics
        trainer = Trainer(
            model=self.intent_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self._compute_classification_metrics,
        )
        
        # Train
        trainer.train()
        
        # Evaluate
        eval_results = trainer.evaluate()
        
        # Save model
        trainer.save_model('./trained_models/intent_classifier')
        
        logger.info(f"Intent classification training completed. F1: {eval_results.get('eval_f1', 0):.4f}")
        
        return eval_results
    
    def train_language_detector(self, train_data: List[Dict], val_data: List[Dict]) -> Dict[str, float]:
        """Train language detection model"""
        logger.info("Training language detection model...")
        
        # Create datasets
        train_dataset = LanguageDetectionDataset(train_data, self.tokenizer)
        val_dataset = LanguageDetectionDataset(val_data, self.tokenizer)
        
        # Initialize model
        self.language_model = AutoModelForSequenceClassification.from_pretrained(
            self.config.get('base_model', 'bert-base-multilingual-cased'),
            num_labels=4  # 4 languages
        ).to(self.device)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir='./language_detector',
            num_train_epochs=self.config.get('language_epochs', 3),
            per_device_train_batch_size=self.config.get('batch_size', 16),
            per_device_eval_batch_size=self.config.get('batch_size', 16),
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=100,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
        )
        
        trainer = Trainer(
            model=self.language_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self._compute_classification_metrics,
        )
        
        # Train
        trainer.train()
        
        # Evaluate
        eval_results = trainer.evaluate()
        
        # Save model
        trainer.save_model('./trained_models/language_detector')
        
        logger.info(f"Language detection training completed. Accuracy: {eval_results.get('eval_accuracy', 0):.4f}")
        
        return eval_results
    
    def train_response_generator(self, train_data: List[Dict], val_data: List[Dict]) -> Dict[str, float]:
        """Train response generation model using fine-tuning"""
        logger.info("Training response generation model...")
        
        # Create datasets
        train_dataset = MultilingualChatbotDataset(train_data, self.tokenizer)
        val_dataset = MultilingualChatbotDataset(val_data, self.tokenizer)
        
        # Initialize model for generation (using BERT as base)
        from transformers import GPT2LMHeadModel, GPT2Tokenizer
        
        # Use GPT-2 for generation if available
        try:
            generation_tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            if generation_tokenizer.pad_token is None:
                generation_tokenizer.pad_token = generation_tokenizer.eos_token
            
            self.response_model = GPT2LMHeadModel.from_pretrained('gpt2').to(self.device)
            
            # Custom training loop for generation
            optimizer = torch.optim.AdamW(self.response_model.parameters(), lr=5e-5)
            scheduler = get_linear_schedule_with_warmup(
                optimizer, 
                num_warmup_steps=100,
                num_training_steps=len(train_dataset) * self.config.get('generation_epochs', 3)
            )
            
            train_loader = DataLoader(train_dataset, batch_size=self.config.get('batch_size', 8), shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.config.get('batch_size', 8))
            
            best_loss = float('inf')
            
            for epoch in range(self.config.get('generation_epochs', 3)):
                # Training
                self.response_model.train()
                total_loss = 0
                
                for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
                    input_ids = batch['input_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels = batch['labels'].to(self.device)
                    
                    optimizer.zero_grad()
                    
                    outputs = self.response_model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    
                    loss = outputs.loss
                    loss.backward()
                    optimizer.step()
                    scheduler.step()
                    
                    total_loss += loss.item()
                
                avg_loss = total_loss / len(train_loader)
                logger.info(f"Epoch {epoch + 1} - Average Loss: {avg_loss:.4f}")
                
                # Validation
                val_loss = self._validate_generation_model(val_loader)
                logger.info(f"Validation Loss: {val_loss:.4f}")
                
                # Save best model
                if val_loss < best_loss:
                    best_loss = val_loss
                    torch.save(self.response_model.state_dict(), './trained_models/response_generator.pt')
            
            eval_results = {'eval_loss': best_loss}
            
        except Exception as e:
            logger.error(f"Response generation training failed: {e}")
            eval_results = {'eval_loss': float('inf')}
        
        return eval_results
    
    def _validate_generation_model(self, val_loader: DataLoader) -> float:
        """Validate response generation model"""
        self.response_model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.response_model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                total_loss += outputs.loss.item()
        
        return total_loss / len(val_loader)
    
    def _compute_classification_metrics(self, eval_pred):
        """Compute classification metrics"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        accuracy = accuracy_score(labels, predictions)
        f1 = f1_score(labels, predictions, average='weighted')
        
        return {
            'accuracy': accuracy,
            'f1': f1
        }
    
    def train_full_pipeline(self, training_data_path: str) -> Dict[str, Dict[str, float]]:
        """Train complete multilingual pipeline"""
        logger.info("Starting full pipeline training...")
        
        # Prepare data
        data_splits = self.prepare_training_data(training_data_path)
        train_data = data_splits['train']
        val_data = data_splits['validation']
        
        results = {}
        
        # Train intent classifier
        intent_results = self.train_intent_classifier(train_data, val_data)
        results['intent_classification'] = intent_results
        
        # Train language detector
        lang_results = self.train_language_detector(train_data, val_data)
        results['language_detection'] = lang_results
        
        # Train response generator
        response_results = self.train_response_generator(train_data, val_data)
        results['response_generation'] = response_results
        
        # Save training history
        self._save_training_results(results)
        
        logger.info("Full pipeline training completed!")
        return results
    
    def _save_training_results(self, results: Dict[str, Dict[str, float]]):
        """Save training results and metrics"""
        os.makedirs('./trained_models', exist_ok=True)
        
        # Save results
        results_path = f'./trained_models/training_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save model configuration
        config_path = './trained_models/model_config.json'
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Training results saved to {results_path}")
    
    def evaluate_model(self, test_data_path: str) -> Dict[str, float]:
        """Evaluate trained models on test data"""
        logger.info("Evaluating trained models...")
        
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        test_conversations = test_data['conversations']
        
        # Load trained models
        self._load_trained_models()
        
        # Evaluate each component
        results = {}
        
        # Intent classification evaluation
        if self.intent_model:
            intent_accuracy = self._evaluate_intent_classification(test_conversations)
            results['intent_accuracy'] = intent_accuracy
        
        # Language detection evaluation
        if self.language_model:
            language_accuracy = self._evaluate_language_detection(test_conversations)
            results['language_accuracy'] = language_accuracy
        
        # End-to-end evaluation
        end_to_end_score = self._evaluate_end_to_end(test_conversations[:100])  # Sample
        results['end_to_end_score'] = end_to_end_score
        
        return results
    
    def _load_trained_models(self):
        """Load trained models for evaluation"""
        try:
            # Load intent classifier
            self.intent_model = AutoModelForSequenceClassification.from_pretrained(
                './trained_models/intent_classifier'
            ).to(self.device)
            
            # Load language detector
            self.language_model = AutoModelForSequenceClassification.from_pretrained(
                './trained_models/language_detector'
            ).to(self.device)
            
            # Load response generator
            if os.path.exists('./trained_models/response_generator.pt'):
                from transformers import GPT2LMHeadModel
                self.response_model = GPT2LMHeadModel.from_pretrained('gpt2').to(self.device)
                self.response_model.load_state_dict(
                    torch.load('./trained_models/response_generator.pt', map_location=self.device)
                )
            
            logger.info("Trained models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading trained models: {e}")
    
    def _evaluate_intent_classification(self, test_conversations: List[Dict]) -> float:
        """Evaluate intent classification accuracy"""
        correct = 0
        total = 0
        
        self.intent_model.eval()
        
        with torch.no_grad():
            for conv in test_conversations:
                encoding = self.tokenizer(
                    conv['user_message'],
                    max_length=256,
                    padding='max_length',
                    truncation=True,
                    return_tensors='pt'
                ).to(self.device)
                
                outputs = self.intent_model(**encoding)
                predicted_intent_id = torch.argmax(outputs.logits, dim=-1).item()
                
                # Map back to intent (simplified)
                intent_mapping = {0: 'greeting', 1: 'craft_search', 2: 'location_search', 
                                3: 'artist_search', 4: 'help_request', 5: 'contact_info',
                                6: 'statistics', 7: 'general_query'}
                
                predicted_intent = intent_mapping.get(predicted_intent_id, 'general_query')
                
                if predicted_intent == conv['intent']:
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0
    
    def _evaluate_language_detection(self, test_conversations: List[Dict]) -> float:
        """Evaluate language detection accuracy"""
        correct = 0
        total = 0
        
        self.language_model.eval()
        
        with torch.no_grad():
            for conv in test_conversations:
                encoding = self.tokenizer(
                    conv['user_message'],
                    max_length=256,
                    padding='max_length',
                    truncation=True,
                    return_tensors='pt'
                ).to(self.device)
                
                outputs = self.language_model(**encoding)
                predicted_lang_id = torch.argmax(outputs.logits, dim=-1).item()
                
                # Map back to language
                lang_mapping = {0: 'english', 1: 'hindi', 2: 'tamil', 3: 'telugu'}
                predicted_lang = lang_mapping.get(predicted_lang_id, 'english')
                
                if predicted_lang == conv['language']:
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0
    
    def _evaluate_end_to_end(self, test_conversations: List[Dict]) -> float:
        """Evaluate end-to-end performance"""
        # Simplified end-to-end evaluation
        # In practice, this would involve more sophisticated metrics
        
        scores = []
        
        for conv in test_conversations:
            try:
                # Simple matching score based on keyword overlap
                user_msg = conv['user_message'].lower()
                expected_response = conv['bot_response'].lower()
                
                # Extract keywords
                user_keywords = set(user_msg.split())
                response_keywords = set(expected_response.split())
                
                # Calculate overlap score
                if len(response_keywords) > 0:
                    overlap = len(user_keywords.intersection(response_keywords))
                    score = overlap / len(response_keywords)
                    scores.append(score)
                    
            except Exception as e:
                logger.warning(f"Error in end-to-end evaluation: {e}")
                scores.append(0)
        
        return np.mean(scores) if scores else 0

# Training configuration
TRAINING_CONFIG = {
    'base_model': 'bert-base-multilingual-cased',
    'batch_size': 16,
    'intent_epochs': 5,
    'language_epochs': 3,
    'generation_epochs': 3,
    'learning_rate': 5e-5,
    'max_length': 512,
    'warmup_steps': 500,
    'weight_decay': 0.01
}

# Main training script
if __name__ == "__main__":
    # Initialize trainer
    trainer = MultilingualTrainer(TRAINING_CONFIG)
    
    # Generate training data if it doesn't exist
    if not os.path.exists('multilingual_training_data.json'):
        logger.info("Generating training data...")
        from multilingual_training_data import MultilingualTrainingDataGenerator
        
        generator = MultilingualTrainingDataGenerator()
        conversations = generator.generate_training_conversations(2000)
        knowledge_base = generator.generate_craft_knowledge_base()
        generator.save_training_data(conversations, knowledge_base)
    
    # Train complete pipeline
    results = trainer.train_full_pipeline('multilingual_training_data.json')
    
    print("\n" + "="*50)
    print("TRAINING RESULTS SUMMARY")
    print("="*50)
    
    for task, metrics in results.items():
        print(f"\n{task.upper()}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
    
    print("\n" + "="*50)
    print("Training completed! Models saved to './trained_models/'")
    print("="*50)