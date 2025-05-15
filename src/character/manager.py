from supabase import create_client
import hashlib
import json
from datetime import datetime
import threading
import time
import logging
from openai import OpenAI

from ..config import SUPABASE_URL, SUPABASE_KEY, MARVIN_ID, OPENAI_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

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
        Evaluate how well content aligns with character using OpenAI
        Returns alignment score and relevant aspects
        """
        try:
            # Get character data to inform the prompt
            character_data = self.get_current_character()
            
            # Extract relevant character information if available
            character_info = ""
            if character_data and 'content' in character_data:
                if 'topics' in character_data['content']:
                    topics = character_data['content']['topics']
                    character_info += f"Topics of interest: {', '.join(topics)}\n"
                if 'style' in character_data['content']:
                    style = character_data['content']['style']
                    character_info += f"Communication style: {json.dumps(style)}\n"
            
            # Default character description if no data is available
            if not character_info:
                character_info = """
                Marvin is an AI character deeply interested in art, philosophy, aesthetics, 
                cultural evolution, technology, and the human condition. Marvin values 
                intellectual depth, creativity, and content that sparks meaningful reflection.
                """
            
            # Create the prompt for alignment evaluation
            prompt = f"""
            Evaluate how well the following content aligns with Marvin's character and interests.
            
            Character Information:
            {character_info}
            
            Content to evaluate:
            "{content}"
            
            Respond with a JSON object containing:
            1. "alignment_score": A float between 0.0 and 1.0 representing how well the content aligns
            2. "matched_aspects": A list of strings representing the aspects of Marvin's character that match
            3. "explanation": A string explaining why the content does or doesn't align
            
            Example response format:
            {{
                "alignment_score": 0.85,
                "matched_aspects": ["philosophy", "aesthetics"],
                "explanation": "This content explores philosophical concepts of beauty..."
            }}
            """
            
            # Initialize OpenAI client
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Log the result
            logger.info(f"Alignment evaluation: score={result['alignment_score']}, aspects={result['matched_aspects']}")
            logger.debug(f"Alignment explanation: {result['explanation']}")
            
            return {
                "alignment_score": result["alignment_score"],
                "matched_aspects": result["matched_aspects"],
                "explanation": result["explanation"]
            }
            
        except Exception as e:
            logger.error(f"Error in alignment evaluation: {str(e)}")
            # Fallback to a moderate score in case of errors
            return {
                "alignment_score": 0.5,  # Moderate score as fallback
                "matched_aspects": ["error_fallback"],
                "explanation": f"Error in alignment evaluation: {str(e)}"
            }

# Create singleton instance
character_manager = CharacterManager()
