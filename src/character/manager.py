from supabase import create_client
import hashlib
import json
from datetime import datetime
import threading
import time

from ..config import SUPABASE_URL, SUPABASE_KEY, MARVIN_ID

class CharacterManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.character_data = None
        self.character_hash = None
        self._load_character()
        self._start_polling()
    
    def _load_character(self):
        """Load character data from Supabase"""
        response = self.supabase.table('character_files') \
            .select('*') \
            .eq('id', MARVIN_ID) \
            .execute()
        
        if response.data:
            self.character_data = response.data[0]
            self.character_hash = self._get_hash(self.character_data)
    
    def _get_hash(self, data):
        """Generate hash of character data"""
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
    
    def _poll_for_changes(self):
        """Poll for character changes"""
        while True:
            try:
                self._load_character()
                new_hash = self._get_hash(self.character_data)
                
                if new_hash != self.character_hash:
                    print(f"Character update detected at {datetime.now()}")
                    # Trigger any necessary updates
                    self.character_hash = new_hash
                
                time.sleep(300)  # Poll every 5 minutes
                
            except Exception as e:
                print(f"Error polling character changes: {e}")
                time.sleep(60)  # Wait before retry
    
    def _start_polling(self):
        """Start polling in background thread"""
        polling_thread = threading.Thread(
            target=self._poll_for_changes,
            daemon=True
        )
        polling_thread.start()
    
    def get_current_character(self):
        """Get current character data"""
        return self.character_data
    
    def get_topics(self):
        """Get character's topics of interest"""
        return self.character_data.get('content', {}).get('topics', [])
    
    def get_style(self):
        """Get character's communication style"""
        return self.character_data.get('content', {}).get('style', {})
    
    def evaluate_alignment(self, content):
        """
        Evaluate how well content aligns with character
        Returns alignment score and relevant aspects
        """
        # TODO: Implement alignment evaluation using LLM
        pass

# Create singleton instance
character_manager = CharacterManager() 