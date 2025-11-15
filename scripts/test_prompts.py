#!/usr/bin/env python3
"""
Test script to verify prompt loading and Langfuse integration

This script:
1. Tests loading prompts from local files
2. Verifies prompt content
3. Tests Langfuse prompt manager initialization
4. Optionally uploads prompts to Langfuse
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompts import load_prompt, get_available_prompts
from src.utils.langfuse_prompts import LangfusePromptManager


def test_local_prompts():
    """Test loading prompts from local files"""
    print("=" * 60)
    print("Testing Local Prompt Loading")
    print("=" * 60)
    
    available_prompts = get_available_prompts()
    print(f"\n✅ Found {len(available_prompts)} prompt files: {available_prompts}\n")
    
    for agent_name in available_prompts:
        try:
            prompt_content = load_prompt(agent_name)
            print(f"📝 {agent_name}:")
            print(f"   - Length: {len(prompt_content)} characters")
            print(f"   - First 100 chars: {prompt_content[:100]}...")
            print(f"   ✅ Loaded successfully\n")
        except Exception as e:
            print(f"   ❌ Failed to load: {e}\n")
    
    return True


def test_langfuse_manager():
    """Test Langfuse prompt manager initialization"""
    print("=" * 60)
    print("Testing Langfuse Prompt Manager")
    print("=" * 60)
    
    try:
        manager = LangfusePromptManager()
        print(f"\n✅ LangfusePromptManager initialized")
        print(f"   - Client available: {manager.client is not None}")
        
        if manager.client:
            print("\n🎯 Langfuse is configured and ready!")
            print("   You can now upload prompts using:")
            print("   python scripts/manage_prompts.py upload")
        else:
            print("\n⚠️  Langfuse client not available")
            print("   - Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
            print("   - Prompts will fall back to local files")
        
        return True
    except Exception as e:
        print(f"\n❌ Failed to initialize LangfusePromptManager: {e}")
        return False


def test_prompt_fetch():
    """Test fetching a prompt (from Langfuse or fallback to local)"""
    print("\n" + "=" * 60)
    print("Testing Prompt Fetch (Langfuse with Local Fallback)")
    print("=" * 60)
    
    manager = LangfusePromptManager()
    
    test_prompts = [
        ("research-agent-prompt", "production"),
        ("protocol-agent-prompt", "production"),
        ("automate-agent-prompt", "production"),
        ("safety-agent-prompt", "production")
    ]
    
    for prompt_name, label in test_prompts:
        try:
            result = manager.get_prompt(prompt_name, label=label)
            
            if result["prompt"]:
                source = "Langfuse" if result.get("version") else "Local File"
                print(f"\n📥 {prompt_name}:")
                print(f"   - Source: {source}")
                if result.get("version"):
                    print(f"   - Version: {result['version']}")
                print(f"   - Length: {len(result['prompt'])} characters")
                print(f"   - Config: {result.get('config', {})}")
                print(f"   ✅ Fetched successfully")
            else:
                print(f"\n⚠️  {prompt_name}: No prompt found (will use base agent fallback)")
                
        except Exception as e:
            print(f"\n❌ {prompt_name}: Failed to fetch - {e}")
    
    return True


def main():
    """Run all tests"""
    print("\n[TEST] Catalyze Prompt Testing Suite\n")
    
    # Test 1: Local prompt loading
    test_local_prompts()
    
    # Test 2: Langfuse manager initialization
    test_langfuse_manager()
    
    # Test 3: Prompt fetching with fallback
    test_prompt_fetch()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If Langfuse is configured, upload prompts:")
    print("   python scripts/manage_prompts.py upload")
    print("\n2. Test A/B testing:")
    print("   python scripts/manage_prompts.py setup-ab-test research-agent-prompt")
    print("\n3. View prompt details:")
    print("   python scripts/manage_prompts.py get research-agent-prompt")
    print()


if __name__ == "__main__":
    main()

