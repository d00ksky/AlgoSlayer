#!/bin/bash
# Setup SSH access for Claude to connect to AlgoSlayer server
# This will enable passwordless SSH access for better workflow

set -e

echo "🔐 Setting up SSH access for Claude to connect to root@64.226.96.90"
echo "=" * 60

# Server details
SERVER_IP="64.226.96.90"
SERVER_USER="root"

# Generate SSH key pair if it doesn't exist
SSH_KEY_PATH="$HOME/.ssh/claude_algoslayer_key"

if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "🔑 Generating new SSH key pair..."
    ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "claude-algoslayer-access"
    echo "✅ SSH key generated: $SSH_KEY_PATH"
else
    echo "✅ SSH key already exists: $SSH_KEY_PATH"
fi

# Display the public key
echo -e "\n📋 Public key to add to server:"
echo "=" * 60
cat "${SSH_KEY_PATH}.pub"
echo "=" * 60

# Create SSH config entry
SSH_CONFIG="$HOME/.ssh/config"
echo -e "\n⚙️  Setting up SSH config..."

# Check if entry already exists
if ! grep -q "Host algoslayer" "$SSH_CONFIG" 2>/dev/null; then
    echo -e "\nHost algoslayer\n    HostName $SERVER_IP\n    User $SERVER_USER\n    IdentityFile $SSH_KEY_PATH\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null" >> "$SSH_CONFIG"
    echo "✅ SSH config entry added"
else
    echo "✅ SSH config entry already exists"
fi

echo -e "\n📝 Next steps to complete setup:"
echo "1. Copy the public key shown above"
echo "2. SSH to your server manually: ssh root@$SERVER_IP"
echo "3. Add the key to authorized_keys:"
echo "   echo 'YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo "4. Ensure SSH permits root login without password:"
echo "   sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config"
echo "   systemctl restart sshd"
echo ""
echo "5. Test the connection: ssh algoslayer"

echo -e "\n🚀 Once setup is complete, Claude can connect using: ssh algoslayer"