import re
import math
from collections import Counter

# Standard English stopwords for lightweight extractive summarization
STOPWORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", 
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", 
    "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", 
    "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", 
    "for", "with", "about", "against", "between", "into", "through", "during", "before", 
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", 
    "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", 
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", 
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", 
    "will", "just", "don", "should", "now"
])

class LocalAnalyzer:
    def __init__(self, team_members=None):
        """
        Initialize the analyzer with an optional list of team member names.
        team_members: list of strings (e.g. ["Alice", "Bob", "Charlie"])
        """
        self.team_members = team_members or []
        self.team_members_lower = [name.lower() for name in self.team_members]

    def clean_text(self, text):
        # Remove extra whitespaces
        return re.sub(r'\s+', ' ', text).strip()

    def split_sentences(self, text):
        # A simple sentence tokenizer using regex
        # Avoid splitting on common abbreviations like Mr., Dr., etc.
        sentence_end = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
        sentences = sentence_end.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def summarize_extractive(self, text, num_sentences=4):
        """
        Performs TF-IDF style extractive summarization.
        No API key or external model downloads needed. Extremely fast and lightweight.
        """
        if not text:
            return ""
            
        sentences = self.split_sentences(text)
        if len(sentences) <= num_sentences:
            return text

        # Tokenize and clean words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in STOPWORDS]
        
        if not words:
            return " ".join(sentences[:num_sentences])

        # Compute word frequencies
        word_freq = Counter(words)
        max_freq = max(word_freq.values())
        
        # Normalize frequencies
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq

        # Score sentences
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
            score = 0
            for w in sentence_words:
                if w in word_freq:
                    score += word_freq[w]
            # Normalize by sentence length to not penalize shorter sentences, but favor content
            sentence_scores[i] = score / (math.log(len(sentence_words) + 1) + 1)

        # Get top sentences
        top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        top_indices.sort() # Keep original order

        summary_sentences = [sentences[idx] for idx in top_indices]
        return " ".join(summary_sentences)

    def extract_action_items(self, text):
        """
        Parses transcripts to find action items, assignees, and deadlines.
        """
        action_items = []
        if not text:
            return action_items

        # Split by newlines first to preserve speaker dialogue turns
        lines = text.split('\n')
        
        # List of verbs that suggest actions
        action_verbs = [
            "send", "email", "mail", "write", "create", "update", "fix", "call", 
            "contact", "schedule", "arrange", "setup", "prepare", "submit", "check", 
            "verify", "review", "test", "develop", "code", "design", "build", "follow up"
        ]
        
        # Deadlines patterns
        deadline_patterns = [
            r'by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'by\s+tomorrow',
            r'by\s+next\s+week',
            r'by\s+the\s+end\s+of\s+(the\s+day|the\s+week|today)',
            r'before\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'due\s+on\s+([a-zA-Z0-9\s/,-]+)',
            r'by\s+(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+|\d{1,2}/\d{1,2})',
            r'\btomorrow\b',
            r'\bnext\s+week\b'
        ]

        # MODALS/INDICATORS
        action_indicators = ["will", "need to", "needs to", "must", "should", "has to", "have to", "todo", "action item", "please"]

        for line_num, line in enumerate(lines):
            line = self.clean_text(line)
            if not line:
                continue

            # Check if there is a speaker (e.g. "Alice: I will do that")
            speaker = None
            dialogue = line
            match_speaker = re.match(r'^([^:\n]+):\s*(.*)$', line)
            if match_speaker:
                speaker = match_speaker.group(1).strip()
                dialogue = match_speaker.group(2).strip()

            # Split dialogue into sentences to analyze individual action statements
            sentences = self.split_sentences(dialogue)
            for sentence in sentences:
                sentence_lower = sentence.lower()
                is_action = False
                
                # Check for action indicator words or explicit patterns
                has_indicator = any(re.search(rf'\b{indicator}\b', sentence_lower) for indicator in action_indicators)
                has_action_verb = any(re.search(rf'\b{verb}\b', sentence_lower) for verb in action_verbs)
                
                if (has_indicator and has_action_verb) or "todo" in sentence_lower or "action item" in sentence_lower or "please" in sentence_lower:
                    is_action = True

                if is_action:
                    # 1. Identify Assignee
                    assignee = "Unassigned"
                    
                    # Try to match name from dialogue text first
                    assigned_name = self._find_name_in_text(sentence)
                    if assigned_name:
                        assignee = assigned_name
                    elif speaker:
                        # If "I will...", speaker is likely the assignee
                        if re.search(r'\bi\s+(will|need\s+to|must|should|have\s+to|can)\b', sentence_lower):
                            assignee = speaker
                        # If the speaker says "You should...", it might be unassigned or refer to someone else, but we fallback
                        else:
                            assignee = speaker

                    # 2. Extract Task Description
                    # Clean up prefix like "I will", "Please", "Action item:"
                    task_desc = sentence
                    # Remove leading speaker name references or "please"
                    task_desc = re.sub(r'^(please|todo:|action\s+item:)\s*', '', task_desc, flags=re.IGNORECASE)
                    
                    # 3. Detect Deadline
                    deadline = "No deadline"
                    for pattern in deadline_patterns:
                        match_dl = re.search(pattern, sentence_lower)
                        if match_dl:
                            deadline = match_dl.group(0).strip()
                            # Clean up deadline prefix for output readability
                            deadline = re.sub(r'^(by|before|due on)\s+', '', deadline, flags=re.IGNORECASE)
                            break
                    
                    # Format assignee nicely
                    if assignee != "Unassigned":
                        assignee = assignee.capitalize()

                    action_items.append({
                        "task": self._clean_task_description(task_desc),
                        "assignee": assignee,
                        "due_date": deadline.capitalize(),
                        "context": line
                    })

        return action_items

    def _find_name_in_text(self, text):
        # Look for explicit name matches from the team directory
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        for word in words:
            word_lower = word.lower()
            if word_lower in self.team_members_lower:
                # Return the original capitalized team member name
                idx = self.team_members_lower.index(word_lower)
                return self.team_members[idx]
        return None

    def _clean_task_description(self, task):
        # Strip trailing/leading punctuation and clean up phrases
        task = re.sub(r'^(i\s+will\s+|we\s+need\s+to\s+|please\s+|could\s+you\s+|we\s+should\s+)', '', task, flags=re.IGNORECASE)
        task = task.strip()
        # Capitalize first letter
        if task:
            task = task[0].upper() + task[1:]
        return task

# Test verification code block (runs only when executed directly)
if __name__ == "__main__":
    sample_transcript = """
Alice: Welcome everyone. Let's discuss our progress.
Bob: I will update the database server by Friday.
Alice: That sounds good. Charlie, please review the frontend mockups tomorrow.
Charlie: Sure, I can do that. I need to coordinate with Dave as well.
Dave: Yes, I will write the API documentation next week.
Alice: Great, that's all for today.
    """
    
    analyzer = LocalAnalyzer(team_members=["Alice", "Bob", "Charlie", "Dave"])
    
    print("--- EXTRACTIVE SUMMARY ---")
    summary = analyzer.summarize_extractive(sample_transcript, num_sentences=2)
    print(summary)
    
    print("\n--- ACTION ITEMS ---")
    actions = analyzer.extract_action_items(sample_transcript)
    for act in actions:
        print(f"Task: {act['task']} | Assignee: {act['assignee']} | Due: {act['due_date']}")
