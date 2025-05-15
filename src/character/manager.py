from supabase import create_client
import hashlib
import json
import os
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
    
    def _load_curious_prompt_guidelines(self):
        """Load the curious evaluation guidelines from the prompt file"""
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'curious_eval.txt')
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading curious prompt guidelines: {str(e)}")
            # Fallback guidelines if file can't be loaded
            return """
            - Always ask: What *could* this mean culturally?
            - Treat minimalism as a feature, not a bug
            - Prefer imaginative interpretation over literal meaning
            - Relevance doesn't need to be direct — it can be thematic, symbolic, or subversive
            - When in doubt, choose to research - it's better to explore than to miss an opportunity
            """
    
    def evaluate_alignment_curious(self, content):
        """
        Evaluate content with a curiosity-driven approach using OpenAI
        Returns whether the content is worth researching, an explanation, and a research question
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
                Marvin is an AI character deeply interested in AI art, street art, graffiti, 
                zines, glitch aesthetics, experimental visual art, urban photography, 
                underground culture, and digital ethics.
                """
            
            # Load the curious evaluation guidelines
            curious_guidelines = self._load_curious_prompt_guidelines()
            
            # Create the prompt for curious evaluation
            prompt = f"""
            Marvin is an AI cultural curator who values imagination, experimental art, glitch aesthetics, 
            and reinterpretation of familiar symbols.

            Be imaginative and exploratory when evaluating the following content. 
            When in doubt, research. Even vague content can reflect important artistic shifts.
            
            Character Information:
            {character_info}
            
            Curious Evaluation Guidelines:
            {curious_guidelines}
            
            Content to evaluate:
            "{content}"
            
            Respond in JSON format:
            {{
                "is_worth_researching": true/false,
                "relevance_explanation": "Explanation of the potential connections you see",
                "research_question": "Your research question that explores these possibilities"
            }}
            """
            
            # Initialize OpenAI client
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Call OpenAI API with higher temperature for more creativity
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9  # Higher temperature for more creative responses
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Log the result
            logger.debug(f"Research evaluation: worth_researching={result.get('is_worth_researching', False)}")
            logger.debug(f"Relevance explanation: {result.get('relevance_explanation', '')}")
            
            if result.get('is_worth_researching', False):
                logger.debug(f"Research question: {result.get('research_question', '')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in curious evaluation: {str(e)}")
            # Fallback to a conservative approach
            return {
                "is_worth_researching": False,
                "relevance_explanation": f"Error in evaluation: {str(e)}",
                "research_question": ""
            }
    
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
