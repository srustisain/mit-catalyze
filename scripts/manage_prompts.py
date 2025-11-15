#!/usr/bin/env python3
"""
Langfuse Prompt Management CLI

This script provides command-line utilities for managing prompts in Langfuse:
- Upload local prompts to Langfuse
- Create new prompt versions
- Promote prompts to production
- A/B testing setup
- Backup and restore prompts

Usage:
    python scripts/manage_prompts.py upload
    python scripts/manage_prompts.py create-version research-agent-prompt "New prompt content" --label staging
    python scripts/manage_prompts.py promote research-agent-prompt 3
    python scripts/manage_prompts.py setup-ab-test research-agent-prompt
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.langfuse_prompts import LangfusePromptManager


class PromptCLI:
    """Command-line interface for Langfuse prompt management"""
    
    def __init__(self):
        self.manager = LangfusePromptManager()
        
    def upload_prompts(self, prompts_dir: str = "src/prompts") -> None:
        """Upload all local prompt files to Langfuse"""
        print("🚀 Uploading local prompts to Langfuse...")
        
        results = self.manager.upload_local_prompts(prompts_dir)
        
        if not results:
            print("❌ No prompts found or upload failed")
            return
        
        print(f"\n📊 Upload Results:")
        for agent_name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  {agent_name}: {status}")
        
        successful_uploads = sum(results.values())
        total_prompts = len(results)
        print(f"\n🎯 Summary: {successful_uploads}/{total_prompts} prompts uploaded successfully")
        
        if successful_uploads > 0:
            print("\n💡 Next steps:")
            print("  1. Visit your Langfuse project to view the uploaded prompts")
            print("  2. Edit prompts in the UI to create new versions")
            print("  3. Use labels (production, staging) for deployment control")
            print("  4. Set up A/B testing with: python scripts/manage_prompts.py setup-ab-test <prompt-name>")
    
    def create_version(self, 
                      prompt_name: str, 
                      content: str,
                      label: Optional[str] = None,
                      config_file: Optional[str] = None,
                      commit_message: Optional[str] = None) -> None:
        """Create a new version of a prompt"""
        print(f"📝 Creating new version of {prompt_name}...")
        
        # Load config if provided
        config = {}
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"📋 Loaded config from {config_file}")
            except Exception as e:
                print(f"⚠️  Failed to load config: {e}")
        
        # Create the prompt version
        labels = [label] if label else []
        success = self.manager.create_prompt_version(
            prompt_name=prompt_name,
            prompt_content=content,
            config=config,
            labels=labels,
            commit_message=commit_message
        )
        
        if success:
            print(f"✅ Successfully created new version of {prompt_name}")
            if label:
                print(f"🏷️  Applied label: {label}")
        else:
            print(f"❌ Failed to create version of {prompt_name}")
    
    def promote_prompt(self, prompt_name: str, version: int) -> None:
        """Promote a prompt version to production"""
        print(f"🚀 Promoting {prompt_name} version {version} to production...")
        
        success = self.manager.promote_to_production(prompt_name, version)
        
        if success:
            print(f"✅ Successfully promoted {prompt_name} v{version} to production")
            print("💡 Note: Complete the promotion in the Langfuse UI by adding the 'production' label")
        else:
            print(f"❌ Failed to promote {prompt_name}")
    
    def setup_ab_test(self, prompt_name: str) -> None:
        """Set up A/B testing for a prompt"""
        print(f"🧪 Setting up A/B testing for {prompt_name}...")
        
        print("""
📋 A/B Testing Setup Instructions:

1. Create two versions of your prompt in Langfuse UI:
   - Version A: Add label 'production-a'
   - Version B: Add label 'production-b'

2. Enable A/B testing in your application:
   Add 'ab_test': True to the context when calling agents

3. Monitor results in Langfuse:
   - View prompt performance metrics
   - Compare response quality between versions
   - Analyze user engagement and success rates

4. Example usage in code:
   context = {
       'ab_test': True,
       'session_id': 'user-session-123'
   }
   
   # The system will randomly select between production-a and production-b
   response = await agent.process_query(query, context)

5. Promote the winning version:
   python scripts/manage_prompts.py promote {prompt_name} <winning_version>
        """)
    
    def backup_prompts(self, output_file: str = "prompts_backup.json") -> None:
        """Backup all prompts to a JSON file"""
        print(f"💾 Backing up prompts to {output_file}...")
        
        # Note: This would need the list prompts API
        print("⚠️  Backup feature requires Langfuse list prompts API")
        print("💡 For now, use the Langfuse UI to export prompts manually")
    
    def test_prompt(self, prompt_name: str, test_query: str, label: str = "production") -> None:
        """Test a prompt with a sample query"""
        print(f"🧪 Testing {prompt_name} with label '{label}'...")
        
        prompt_data = self.manager.get_prompt_with_config(prompt_name, label=label)
        
        if not prompt_data["prompt"]:
            print(f"❌ Prompt {prompt_name} not found with label '{label}'")
            return
        
        print(f"📋 Prompt version: {prompt_data.get('version', 'unknown')}")
        print(f"🏷️  Label: {label}")
        print(f"⚙️  Config: {json.dumps(prompt_data.get('config', {}), indent=2)}")
        print(f"\n📝 Prompt content:")
        print("-" * 50)
        print(prompt_data["prompt"])
        print("-" * 50)
        print(f"\n🔍 Test query: {test_query}")
        print("💡 Use this prompt in your agent to see the full response")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Langfuse Prompt Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_prompts.py upload
  python scripts/manage_prompts.py create-version research-agent-prompt "New content" --label staging
  python scripts/manage_prompts.py promote research-agent-prompt 3
  python scripts/manage_prompts.py setup-ab-test research-agent-prompt
  python scripts/manage_prompts.py test research-agent-prompt "What is caffeine?" --label production
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload local prompts to Langfuse')
    upload_parser.add_argument('--dir', default='src/prompts', help='Directory containing prompt files')
    
    # Create version command
    create_parser = subparsers.add_parser('create-version', help='Create a new prompt version')
    create_parser.add_argument('prompt_name', help='Name of the prompt in Langfuse')
    create_parser.add_argument('content', help='Prompt content (or @filename to read from file)')
    create_parser.add_argument('--label', help='Label to assign (e.g., staging, production)')
    create_parser.add_argument('--config', help='JSON config file path')
    create_parser.add_argument('--message', help='Commit message')
    
    # Promote command
    promote_parser = subparsers.add_parser('promote', help='Promote prompt version to production')
    promote_parser.add_argument('prompt_name', help='Name of the prompt in Langfuse')
    promote_parser.add_argument('version', type=int, help='Version number to promote')
    
    # A/B test setup command
    ab_parser = subparsers.add_parser('setup-ab-test', help='Set up A/B testing for a prompt')
    ab_parser.add_argument('prompt_name', help='Name of the prompt in Langfuse')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup all prompts to JSON file')
    backup_parser.add_argument('--output', default='prompts_backup.json', help='Output file path')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a prompt with sample query')
    test_parser.add_argument('prompt_name', help='Name of the prompt in Langfuse')
    test_parser.add_argument('query', help='Test query')
    test_parser.add_argument('--label', default='production', help='Prompt label to test')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = PromptCLI()
    
    try:
        if args.command == 'upload':
            cli.upload_prompts(args.dir)
        
        elif args.command == 'create-version':
            content = args.content
            # Handle @filename syntax
            if content.startswith('@'):
                file_path = content[1:]
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    print(f"📖 Read content from {file_path}")
                except Exception as e:
                    print(f"❌ Failed to read file {file_path}: {e}")
                    return
            
            cli.create_version(
                args.prompt_name, 
                content, 
                args.label, 
                args.config, 
                args.message
            )
        
        elif args.command == 'promote':
            cli.promote_prompt(args.prompt_name, args.version)
        
        elif args.command == 'setup-ab-test':
            cli.setup_ab_test(args.prompt_name)
        
        elif args.command == 'backup':
            cli.backup_prompts(args.output)
        
        elif args.command == 'test':
            cli.test_prompt(args.prompt_name, args.query, args.label)
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
