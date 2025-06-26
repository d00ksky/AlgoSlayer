#!/bin/bash
# Script to remove passphrase from SSH key

echo "🔓 Removing passphrase from SSH key"
echo "You'll need to enter your current passphrase when prompted"
echo ""

# This will prompt for current passphrase and then remove it
ssh-keygen -p -f ~/.ssh/id_rsa

echo ""
echo "✅ If successful, the passphrase has been removed!"
echo "🔧 Now testing SSH connection..."

# Test the connection
ssh -o BatchMode=yes -o ConnectTimeout=5 root@64.226.96.90 "echo '✅ SSH connection successful!'; hostname; date" || echo "❌ Connection failed"