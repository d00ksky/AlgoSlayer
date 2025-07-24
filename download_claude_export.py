#!/usr/bin/env python3
"""
Download Claude Code's Exported Data
Quick script to download the training data Claude Code prepared
"""
import asyncio
from enhanced_hybrid_coordinator import HybridCoordinator

async def main():
    coordinator = HybridCoordinator()
    
    print("🤝 Connecting to server to download Claude Code's export...")
    success = await coordinator.download_claude_code_export()
    
    if success:
        print("✅ Export download successful!")
        print("📁 Check hybrid_work/data_export/ for files")
    else:
        print("❌ Export download failed")
        print("🔄 Trying fallback database sync...")
        
        # Fallback to regular sync
        analysis = await coordinator.sync_and_analyze_server_data()
        if analysis:
            print("✅ Fallback sync successful!")
        else:
            print("❌ All sync methods failed")

if __name__ == "__main__":
    asyncio.run(main())