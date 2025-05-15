🛠️ Step-by-Step Guide to Implementing Marvin’s LLM-Based Enhancements
✅ Phase 1: Setup and Groundwork
1.1 ⬇️ Install Required Dependencies (if not done already)
In your Dockerfile or virtual environment:

bash
Copy
Edit
pip install openai
1.2 🔐 Configure Environment Variables
Update your .env:

dotenv
Copy
Edit
OPENAI_API_KEY=your-openai-key
Update config.py to include:

python
Copy
Edit
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
✅ Phase 2: Improve Alignment Evaluation
2.1 🧠 Update character_manager.py
➕ Add OpenAI integration
python
Copy
Edit
# character_manager.py
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def evaluate_alignment(tweet: str) -> dict:
    prompt = f"""
    Marvin is an AI character deeply interested in art, philosophy, aesthetics, and cultural evolution.
    Evaluate the tweet below. Respond with:
    {{
        "score": float,          # from 0.0 to 1.0
        "aspects": [str],        # what aspects aligned
        "explanation": str       # why it aligns or not
    }}

    Tweet: "{tweet}"
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"score": 0.5, "aspects": [], "explanation": f"Error fallback: {e}"}
2.2 ✅ Test This Function
Add test cases in test_character_manager.py:

python
Copy
Edit
def test_alignment_high_score():
    result = evaluate_alignment("Art is the purest form of rebellion.")
    assert result["score"] > 0.7
✅ Phase 3: Enhance Research Queries
3.1 🧪 Modify tweet_processor/research.py
python
Copy
Edit
def generate_research_query(tweet_text: str) -> str:
    prompt = f"""
    Marvin is an AI researching culture and philosophy. Based on this tweet, generate a culturally insightful research question:

    Tweet: "{tweet_text}"
    Research Question:
    """
    result = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return result.choices[0].message.content.strip()
3.2 ✅ Integrate With research_tweet()
In your tweet processor logic:

python
Copy
Edit
if alignment["score"] >= 0.75:
    query = generate_research_query(tweet_text)
    research_output = call_perplexity_api(query)
✅ Phase 4: Improve Tweet Processing Pipeline
4.1 🔄 Update Tweet Filtering Logic
In tweet_processor.py:

Pull top tweets from tweets_cache

Skip tweets below alignment threshold

Prevent duplicates using tweet ID checks in metadata

python
Copy
Edit
if not already_in_memory(tweet_id) and alignment["score"] > 0.75:
    # Proceed with embedding, storing, etc.
4.2 🧬 Store Full Metadata in Memory System
Update your Qdrant memory storage logic:

python
Copy
Edit
memory_entry = {
    "id": str(uuid.uuid4()),
    "type": "research",
    "source": f"tweet:{tweet_id}",
    "content": research_output,
    "tags": alignment["aspects"],
    "timestamp": now().isoformat(),
    "agent_id": "marvin",
    "alignment_score": alignment["score"],
    "alignment_reason": alignment["explanation"]
}
✅ Phase 5: Testing & Logging
5.1 🧪 Add Unit Tests
In test_processor.py:

Test high- and low-alignment tweets

Mock LLM calls

Validate Qdrant write format

5.2 📝 Add Logs
In tweet_processor.py:

python
Copy
Edit
logger.info(f"Tweet aligned: {alignment['score']} - {alignment['explanation']}")
logger.debug(f"Generated research query: {query}")
✅ Phase 6: Monitor and Optimize
6.1 📊 Track Alignment Distribution
Log and review:

What percentage of tweets are above threshold?

Which topics dominate “aligned” categories?

6.2 🔁 Fine-Tune Alignment Thresholds
Adjust:

score > 0.75 → > 0.85 if memory fills too fast

Apply separate threshold for “quote inspiration” vs “research”

🧱 Final Result: System Flow Summary
scss
Copy
Edit
📥 Tweet from Supabase → 
🧠 evaluate_alignment() via GPT-4 →
✅ If aligned →
💡 generate_research_query() via GPT-4 →
📚 Perplexity research →
🧠 Store in Qdrant + Supabase with metadata
✨ Optional Enhancements
Feature	Benefit
Async LLM handling	Prevent delays on GPT timeouts
Caching tweet IDs	Skip already-processed tweets
Vector pruning strategy	Control memory size
Memory scoring dashboards	Visualize memory alignment quality