#!/bin/bash
echo "🔧 Deploying Telegram bot 409 fix..."

# 1. Backup current telegram bot
scp root@64.226.96.90:/opt/rtx-trading/src/core/telegram_bot.py telegram_bot_backup.py
echo "✅ Backed up current telegram_bot.py"

# 2. Deploy enhanced version
scp enhanced_telegram_bot.py root@64.226.96.90:/opt/rtx-trading/src/core/telegram_bot_enhanced.py
echo "✅ Deployed enhanced telegram bot"

# 3. Test the fix
ssh root@64.226.96.90 "cd /opt/rtx-trading && rtx-env/bin/python -c \"
import sys
sys.path.append('/opt/rtx-trading')
from src.core.telegram_bot_enhanced import enhanced_telegram_bot
print('✅ Enhanced bot loaded successfully')
print(f'Bot token configured: {bool(enhanced_telegram_bot.bot_token)}')
print(f'Chat ID configured: {bool(enhanced_telegram_bot.chat_id)}')
\""

echo "🎯 Fix deployed! To activate:"
echo "1. Stop current service: sudo systemctl stop rtx-trading"
echo "2. Update imports to use enhanced_telegram_bot"
echo "3. Start service: sudo systemctl start rtx-trading"
echo "4. Monitor: journalctl -u rtx-trading -f"
