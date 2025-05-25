#!/usr/bin/env python3
"""
Quick Start Script for Candlestick Nano MVP
Helps you choose and deploy the best trading bot configuration
"""
import os
import sys
import subprocess

def check_env_vars():
    """Check if required environment variables are set"""
    required = [
        "QUICKNODE_ENDPOINT",
        "WALLET_ADDRESS", 
        "WALLET_PRIVATE_KEY"
    ]
    
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Copy .envrc.sample to .envrc and fill in your values")
        print("   Then run: direnv allow")
        return False
    
    return True

def show_options():
    """Display deployment options"""
    print("\n🚀 Candlestick Nano - Quick Start MVP")
    print("=" * 50)
    print("\nChoose your deployment option:\n")
    
    print("1. 🏃 Quick Test (Combined Daemon)")
    print("   - Best for: Testing and development")
    print("   - Cost: Low (just server/local costs)")
    print("   - Setup: Instant")
    print()
    
    print("2. ☁️  Serverless (QuickNode Functions)")
    print("   - Best for: Production with minimal maintenance")
    print("   - Cost: Pay per execution")
    print("   - Setup: Requires QuickNode dashboard configuration")
    print()
    
    print("3. 🛠️  Manual Trading (Legacy Scripts)")
    print("   - Best for: Manual token discovery and trading")
    print("   - Cost: None (manual execution)")
    print("   - Setup: None")
    print()
    
    print("4. 📚 View Documentation")
    print("5. ❌ Exit")

def run_combined_daemon():
    """Run the combined daemon"""
    print("\n🤖 Starting Combined Trading Bot...")
    print("This will monitor pools and execute trades automatically.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        subprocess.run([sys.executable, "combined_daemon.py"])
    except KeyboardInterrupt:
        print("\n✋ Bot stopped.")

def setup_serverless():
    """Guide for serverless setup"""
    print("\n☁️  Serverless Setup Guide")
    print("=" * 50)
    print("\n1. Install QuickNode CLI:")
    print("   npm install -g @quicknode/cli")
    print("   qn login")
    print()
    print("2. Deploy functions:")
    print("   cd quicknode_functions")
    print("   qn function deploy entry_function.js")
    print("   qn function deploy exit_function.js")
    print()
    print("3. Configure triggers in QuickNode dashboard")
    print()
    print("📖 See DEPLOYMENT_GUIDE.md for detailed instructions")

def run_manual_trading():
    """Guide for manual trading"""
    print("\n🛠️  Manual Trading Scripts")
    print("=" * 50)
    print("\n1. Extract token candidates:")
    print("   python extractor.py")
    print()
    print("2. Buy selected tokens:")
    print("   python buy.py")
    print()
    print("3. Monitor positions:")
    print("   python exit_monitor.py")
    print()
    print("Note: These are legacy scripts for manual operation")

def view_docs():
    """Display documentation links"""
    print("\n📚 Documentation")
    print("=" * 50)
    print("\n- README.md - Project overview")
    print("- DEPLOYMENT_GUIDE.md - Detailed deployment instructions")
    print("- INTEGRATION_SUMMARY.md - Technical integration details")
    print("- AGENTS.md - AI agent integration guide")

def main():
    """Main quick start flow"""
    if not check_env_vars():
        return
    
    while True:
        show_options()
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                run_combined_daemon()
            elif choice == "2":
                setup_serverless()
            elif choice == "3":
                run_manual_trading()
            elif choice == "4":
                view_docs()
            elif choice == "5":
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 