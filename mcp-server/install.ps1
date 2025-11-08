# BACOWR MCP Server Installation Script (Windows PowerShell)
#
# This script helps configure Claude Desktop to use BACOWR MCP server on Windows.
#

Write-Host "======================================================================"
Write-Host "BACOWR MCP Server Installation (Windows)"
Write-Host "======================================================================"
Write-Host ""

# Get absolute path to BACOWR directory
$BACOWR_DIR = Split-Path -Parent $PSScriptRoot
$MCP_SERVER_PATH = Join-Path $BACOWR_DIR "mcp-server\server.py"

Write-Host "BACOWR directory: $BACOWR_DIR"
Write-Host "MCP server: $MCP_SERVER_PATH"
Write-Host ""

# Set config path for Windows
$CONFIG_DIR = "$env:APPDATA\Claude"
$CONFIG_FILE = "$CONFIG_DIR\claude_desktop_config.json"

Write-Host "Config file: $CONFIG_FILE"
Write-Host ""

# Create config directory if it doesn't exist
if (!(Test-Path -Path $CONFIG_DIR)) {
    Write-Host "Creating config directory..."
    New-Item -ItemType Directory -Path $CONFIG_DIR -Force | Out-Null
}

# Check if config file exists
if (Test-Path -Path $CONFIG_FILE) {
    Write-Host "⚠️  Config file already exists!" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to backup and overwrite? (y/n)"

    if ($response -match "^[Yy]$") {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BACKUP_FILE = "$CONFIG_FILE.backup.$timestamp"
        Write-Host "Backing up to: $BACKUP_FILE"
        Copy-Item -Path $CONFIG_FILE -Destination $BACKUP_FILE
    } else {
        Write-Host "Installation cancelled. Please manually add BACOWR MCP server to your config."
        Write-Host ""
        Write-Host "Add this to $CONFIG_FILE :"
        Write-Host @"

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
"@
        exit 0
    }
}

# Get API key
Write-Host ""
Write-Host "Enter your Anthropic API key (or press Enter to skip):"
$API_KEY = Read-Host

if ([string]::IsNullOrWhiteSpace($API_KEY)) {
    $API_KEY = "your-api-key-here"
    Write-Host "⚠️  No API key entered. You'll need to add it manually to the config." -ForegroundColor Yellow
}

# Create config file
Write-Host ""
Write-Host "Creating configuration..."

# Convert paths to use forward slashes for JSON
$MCP_SERVER_PATH_JSON = $MCP_SERVER_PATH -replace '\\', '/'
$BACOWR_DIR_JSON = $BACOWR_DIR -replace '\\', '/'

$configContent = @"
{
  "mcpServers": {
    "bacowr": {
      "command": "python",
      "args": [
        "$MCP_SERVER_PATH_JSON"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "$API_KEY",
        "PYTHONPATH": "$BACOWR_DIR_JSON"
      }
    }
  }
}
"@

$configContent | Out-File -FilePath $CONFIG_FILE -Encoding UTF8

Write-Host "✓ Configuration file created" -ForegroundColor Green
Write-Host ""

Write-Host "======================================================================"
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "======================================================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart Claude Desktop"
Write-Host "  2. Open a new conversation"
Write-Host "  3. Ask: 'Can you list available tools?'"
Write-Host "  4. You should see: generate_backlink_article, estimate_cost, get_provider_info"
Write-Host ""

if ($API_KEY -eq "your-api-key-here") {
    Write-Host "⚠️  Remember to add your API key to:" -ForegroundColor Yellow
    Write-Host "  $CONFIG_FILE"
    Write-Host ""
}

Write-Host "Documentation:"
Write-Host "  $BACOWR_DIR\mcp-server\README.md"
Write-Host ""
Write-Host "======================================================================"
