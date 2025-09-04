import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import pickle
import os

class ArtisanDataProcessor:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.embeddings = None
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.load_and_process_data()
    
    def load_and_process_data(self):
        """Load CSV data and preprocess it"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"Loaded {len(self.df)} artisan records")
            
            # Clean and preprocess data
            self.df = self.df.dropna(subset=['name', 'craft_type', 'state', 'district'])
            self.df['languages_spoken'] = self.df['languages_spoken'].fillna('')
            self.df['contact_phone'] = self.df['contact_phone'].astype(str)
            
            # Create combined text for embeddings
            self.df['combined_text'] = (
                self.df['name'] + ' ' +
                self.df['craft_type'] + ' ' +
                self.df['state'] + ' ' +
                self.df['district'] + ' ' +
                self.df['village'] + ' ' +
                self.df['languages_spoken']
            )
            
            # Generate embeddings
            self.generate_embeddings()
            
            print("Data preprocessing completed")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.df = pd.DataFrame()
    
    def generate_embeddings(self):
        """Generate sentence embeddings for all artisans"""
        if self.df.empty:
            return
        
        print("Generating embeddings...")
        combined_texts = self.df['combined_text'].tolist()
        self.embeddings = self.sentence_model.encode(combined_texts)
        print(f"Generated embeddings for {len(self.embeddings)} records")
    
    def categorize_by_state(self) -> Dict[str, List[Dict]]:
        """Categorize artists by state"""
        categories = {}
        for state in self.df['state'].unique():
            state_artists = self.df[self.df['state'] == state]
            categories[state] = state_artists.to_dict('records')
        return categories
    
    def categorize_by_city_and_state(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Categorize artists by state and then by city"""
        categories = {}
        for state in self.df['state'].unique():
            categories[state] = {}
            state_df = self.df[self.df['state'] == state]
            
            for district in state_df['district'].unique():
                district_artists = state_df[state_df['district'] == district]
                categories[state][district] = district_artists.to_dict('records')
        
        return categories
    
    def categorize_by_craft(self) -> Dict[str, List[Dict]]:
        """Categorize artists by craft type"""
        categories = {}
        for craft in self.df['craft_type'].unique():
            craft_artists = self.df[self.df['craft_type'] == craft]
            categories[craft] = craft_artists.to_dict('records')
        return categories
    
    def categorize_by_state_city_craft(self) -> Dict[str, Dict[str, Dict[str, List[Dict]]]]:
        """Categorize artists by state -> city -> craft"""
        categories = {}
        for state in self.df['state'].unique():
            categories[state] = {}
            state_df = self.df[self.df['state'] == state]
            
            for district in state_df['district'].unique():
                categories[state][district] = {}
                district_df = state_df[state_df['district'] == district]
                
                for craft in district_df['craft_type'].unique():
                    craft_artists = district_df[district_df['craft_type'] == craft]
                    categories[state][district][craft] = craft_artists.to_dict('records')
        
        return categories
    
    def find_similar_artists(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find similar artists based on semantic similarity"""
        if self.df.empty or self.embeddings is None:
            return []
        
        # Generate embedding for query
        query_embedding = self.sentence_model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top K similar artists
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            artist = self.df.iloc[idx].to_dict()
            artist['similarity_score'] = float(similarities[idx])
            results.append(artist)
        
        return results
    
    def search_artists(self, filters: Dict[str, Any]) -> List[Dict]:
        """Search artists with various filters"""
        filtered_df = self.df.copy()
        
        if 'state' in filters and filters['state']:
            filtered_df = filtered_df[
                filtered_df['state'].str.contains(filters['state'], case=False, na=False)
            ]
        
        if 'district' in filters and filters['district']:
            filtered_df = filtered_df[
                filtered_df['district'].str.contains(filters['district'], case=False, na=False)
            ]
        
        if 'craft_type' in filters and filters['craft_type']:
            filtered_df = filtered_df[
                filtered_df['craft_type'].str.contains(filters['craft_type'], case=False, na=False)
            ]
        
        if 'name' in filters and filters['name']:
            filtered_df = filtered_df[
                filtered_df['name'].str.contains(filters['name'], case=False, na=False)
            ]
        
        if 'age_min' in filters:
            filtered_df = filtered_df[filtered_df['age'] >= filters['age_min']]
        
        if 'age_max' in filters:
            filtered_df = filtered_df[filtered_df['age'] <= filters['age_max']]
        
        return filtered_df.to_dict('records')
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the dataset"""
        if self.df.empty:
            return {}
        
        return {
            'total_artists': len(self.df),
            'unique_states': len(self.df['state'].unique()),
            'unique_districts': len(self.df['district'].unique()),
            'unique_crafts': len(self.df['craft_type'].unique()),
            'states': sorted(self.df['state'].unique().tolist()),
            'crafts': sorted(self.df['craft_type'].unique().tolist()),
            'age_distribution': {
                'min': int(self.df['age'].min()),
                'max': int(self.df['age'].max()),
                'mean': float(self.df['age'].mean())
            }
        }
    
    def save_model_data(self, path: str):
        """Save processed data and embeddings"""
        data = {
            'df': self.df,
            'embeddings': self.embeddings,
            'stats': self.get_stats()
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"Model data saved to {path}")
    
    def load_model_data(self, path: str):
        """Load processed data and embeddings"""
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.df = data['df']
            self.embeddings = data['embeddings']
            print(f"Model data loaded from {path}")
            return True
        return False