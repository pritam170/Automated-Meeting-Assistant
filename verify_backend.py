import sys
import os

# Add parent dir to path so we can import backend packages
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyzer import LocalAnalyzer
from transcriber import LocalTranscriber

def test_analyzer():
    print("=== Testing LocalAnalyzer ===")
    sample_text = """
    Alice: Welcome everyone. Let's start the weekly sync.
    Bob: I will update the database server by Friday.
    Alice: Excellent. Charlie, please review the frontend mockups tomorrow.
    Charlie: Will do, Alice. I'll make sure to get on it.
    Dave: I will write the API documentation before next week.
    Alice: Thanks everyone, let's work hard.
    """
    
    # Initialize with team members
    team_members = ["Alice", "Bob", "Charlie", "Dave"]
    analyzer = LocalAnalyzer(team_members=team_members)
    
    # 1. Test Summary
    summary = analyzer.summarize_extractive(sample_text, num_sentences=3)
    print("\n[Extractive Summary]")
    print(summary)
    assert len(summary) > 0, "Summary should not be empty"
    
    # 2. Test Action Items
    action_items = analyzer.extract_action_items(sample_text)
    print("\n[Extracted Action Items]")
    for item in action_items:
        print(f"- Task: {item['task']}")
        print(f"  Assignee: {item['assignee']}")
        print(f"  Due Date: {item['due_date']}")
        print(f"  Context: {item['context']}\n")
    
    assert len(action_items) >= 3, "Should have extracted at least 3 action items"
    print("LocalAnalyzer tests passed successfully!\n")

def test_transcriber_fallback():
    print("=== Testing LocalTranscriber Fallback ===")
    transcriber = LocalTranscriber()
    transcript = transcriber.transcribe("dummy_design_meeting.mp3")
    
    print("\n[Simulated Transcript]")
    print(transcript)
    assert "Sarah:" in transcript or "Alice:" in transcript, "Transcript should match dummy text patterns"
    print("LocalTranscriber fallback tests passed successfully!\n")

if __name__ == "__main__":
    try:
        test_analyzer()
        test_transcriber_fallback()
        print("All backend tests COMPLETED successfully!")
    except Exception as e:
        print(f"Test verification FAILED: {e}", file=sys.stderr)
        sys.exit(1)
