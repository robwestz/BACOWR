#!/bin/bash
#
# BACOWR MCP Server Installation Script
#
# This script helps configure Claude Desktop to use BACOWR MCP server.
#

set -e

echo "======================================================================"
echo "BACOWR MCP Server Installation"
echo "======================================================================"
echo ""

# Get absolute path to BACOWR directory
BACOWR_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MCP_SERVER_PATH="$BACOWR_DIR/mcp-server/server.py"

echo "BACOWR directory: $BACOWR_DIR"
echo "MCP server: $MCP_SERVER_PATH"
echo ""

# Detect OS and set config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    OS_NAME="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CONFIG_DIR="$HOME/.config/Claude"
    OS_NAME="Linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CONFIG_DIR="$APPDATA/Claude"
    OS_NAME="Windows"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

echo "OS: $OS_NAME"
echo "Config file: $CONFIG_FILE"
echo ""

# Create config directory if it doesn't exist
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating config directory..."
    mkdir -p "$CONFIG_DIR"
fi

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  Config file already exists!"
    echo ""
    read -p "Do you want to backup and overwrite? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backing up to: $BACKUP_FILE"
        cp "$CONFIG_FILE" "$BACKUP_FILE"
    else
        echo "Installation cancelled. Please manually add BACOWR MCP server to your config."
        echo ""
        echo "Add this to $CONFIG_FILE:"
        cat <<EOF

{
  "mcpServers": {
    "bacowr": {
      "command": "python",
      "args": ["$MCP_SERVER_PATH"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here",
        "PYTHONPATH": "$BACOWR_DIR"
      }
    }
  }
}
EOF
        exit 0
    fi
fi

# Get API key
echo ""
echo "Enter your Anthropic API key (or press Enter to skip):"
read -r API_KEY

if [ -z "$API_KEY" ]; then
    API_KEY="your-api-key-here"
    echo "⚠️  No API key entered. You'll need to add it manually to the config."
fi

# Create config file
echo ""
echo "Creating configuration..."

cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "bacowr": {
      "command": "python",
      "args": [
        "$MCP_SERVER_PATH"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "$API_KEY",
        "PYTHONPATH": "$BACOWR_DIR"
      }
    }
  }
}
EOF

echo "✓ Configuration file created"
echo ""

# Make server executable
chmod +x "$MCP_SERVER_PATH"
echo "✓ Server script is executable"
echo ""

echo "======================================================================"
echo "✅ Installation Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Desktop"
echo "  2. Open a new conversation"
echo "  3. Ask: 'Can you list available tools?'"
echo "  4. You should see: generate_backlink_article, estimate_cost, get_provider_info"
echo ""
echo "If API key was skipped, edit:"
echo "  $CONFIG_FILE"
echo ""
echo "Documentation:"
echo "  $BACOWR_DIR/mcp-server/README.md"
echo ""
echo "======================================================================"
