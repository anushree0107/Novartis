import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from agents.debate_council import DebateCouncil


async def main():
    print("="*60)
    print("🏛️ DEBATE COUNCIL TEST")
    print("="*60)
    
    # Initialize the debate council
    print("\n⏳ Initializing DebateCouncil...")
    try:
        council = DebateCouncil()
        print("✅ DebateCouncil initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize DebateCouncil: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with a known site from the data
    site_id = "Site 2"  # From the CSV data
    print(f"\n🎯 Starting debate for: {site_id}")
    print("-"*60)
    
    try:
        async for event in council.run_debate(site_id):
            speaker = event.get("speaker", "Unknown")
            content = event.get("content", "")
            event_type = event.get("type", "message")
            
            if event_type == "verdict":
                print(f"\n📜 FINAL VERDICT:")
                print(f"   {content}")
            else:
                icon = {"Hawk": "🦅", "Dove": "🕊️", "Owl": "🦉", "System": "🔧"}.get(speaker, "💬")
                print(f"\n{icon} [{speaker}]:")
                print(f"   {content}")
                
    except Exception as e:
        print(f"\n❌ Error during debate: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "="*60)
    print("🏁 Debate completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
