# BACOWR MCP Server

**Model Context Protocol** server for BACOWR content generation.

Allows Claude Desktop users to generate backlink content via **login** instead of API keys.

---

## 🎯 What This Does

Instead of using API keys, users can:
1. Install this MCP server
2. Use Claude Desktop with their subscription
3. Generate BACOWR content directly in conversations
4. No API keys needed (uses Claude Desktop login)

---

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
cd mcp-server
pip install -r ../requirements.txt
```

### 2. Configure Claude Desktop

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "bacowr": {
      "command": "python",
      "args": [
        "/absolute/path/to/BACOWR/mcp-server/server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here",
        "PYTHONPATH": "/absolute/path/to/BACOWR"
      }
    }
  }
}
```

**Important**: Replace paths with your actual absolute paths!

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### 4. Verify Installation

In Claude Desktop, type:
```
Can you list available tools?
```

You should see:
- `generate_backlink_article`
- `estimate_cost`
- `get_provider_info`

---

## 🛠️ Available Tools

### `generate_backlink_article`

Generate SEO-optimized backlink article.

**Parameters**:
- `publisher_domain` (required): Domain where content will be published
- `target_url` (required): URL to link to
- `anchor_text` (required): Anchor text for the link
- `writing_strategy`: "multi_stage" (best) or "single_shot" (fast)
- `country`: Country code for SERP (default: "se")
- `use_ahrefs`: Use Ahrefs API (requires key)

**Example**:
```
Generate a backlink article for:
- Publisher: aftonbladet.se
- Target: https://sv.wikipedia.org/wiki/Artificiell_intelligens
- Anchor: läs mer om AI
- Strategy: multi_stage
```

### `estimate_cost`

Estimate cost before generating.

**Parameters**:
- `writing_strategy` (required): "multi_stage" or "single_shot"
- `num_articles`: Number to estimate (default: 1)

**Example**:
```
Estimate cost for 10 articles using multi_stage strategy
```

### `get_provider_info`

Get information about available LLM providers and strategies.

**Example**:
```
Show me available LLM providers
```

---

## 📖 Usage Examples

### Generate Single Article

```
I need a backlink article:
- Publisher: svd.se
- Target: https://example.com/product
- Anchor: learn more about our product
- Use multi-stage for best quality
```

### Estimate Costs

```
How much would it cost to generate 50 articles with single-shot strategy?
```

### Check Configuration

```
What LLM providers and models are available?
```

---

## 🔧 Configuration

### Environment Variables

Set in `claude_desktop_config.json`:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (for backend LLM calls)
- `OPENAI_API_KEY`: (Optional) For OpenAI models
- `GOOGLE_API_KEY`: (Optional) For Gemini models
- `AHREFS_API_KEY`: (Optional) For real SERP data
- `PYTHONPATH`: Path to BACOWR root directory

### Writing Strategies

**Multi-Stage (Recommended)**:
- 3 LLM calls: Outline → Content → Polish
- Best quality
- ~30-60 seconds
- ~$0.06 per article (with Haiku)

**Single-Shot (Fast)**:
- 1 optimized LLM call
- Good quality
- ~10-20 seconds
- ~$0.02 per article (with Haiku)

---

## 🐛 Troubleshooting

### Server Not Showing Up

1. Check Claude Desktop config file syntax (valid JSON)
2. Verify absolute paths are correct
3. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.config/Claude/logs/`

### "Tool execution failed"

1. Verify PYTHONPATH is set correctly
2. Check API keys are valid
3. Ensure all dependencies installed
4. Check server.py has execute permissions

### Server Crashes

1. Check Claude Desktop logs
2. Run server manually to see errors:
   ```bash
   python server.py
   ```
3. Verify Python version (3.8+)

### No Output from Tools

1. Check ANTHROPIC_API_KEY is set
2. Verify BACOWR code is accessible
3. Check for import errors in logs

---

## 🔄 Development

### Testing Server Manually

```bash
cd mcp-server
python server.py
```

Then send JSON-RPC messages:

```json
{"method": "tools/list", "params": {}}
```

### Debugging

Enable debug mode by setting in config:
```json
{
  "env": {
    "DEBUG": "true"
  }
}
```

---

## 📊 Comparison: API Keys vs MCP

| Feature | API Keys | MCP (This) |
|---------|----------|------------|
| **Setup** | Add key to .env | Configure Claude Desktop |
| **Cost** | Pay per API call | Included in Claude subscription* |
| **Authentication** | API key | Claude Desktop login |
| **Integration** | Any code | Claude Desktop only |
| **Convenience** | Good | Excellent |

*Note: Backend still uses API for LLM calls, but user doesn't manage keys

---

## 🎯 Next Steps

1. **Install** the MCP server (see Quick Setup)
2. **Test** with a simple article generation
3. **Explore** batch processing (via conversation)
4. **Check** PRODUCTION_GUIDE.md for advanced features

---

## 📚 Resources

- **MCP Specification**: https://modelcontextprotocol.io/
- **BACOWR Docs**: See root README.md
- **Claude Desktop**: https://claude.ai/download

---

## 🔒 Security

- Never commit API keys to version control
- Use environment variables for sensitive data
- MCP server runs locally with your permissions
- Data processed through Anthropic (same as API)

---

**Version**: 1.0.0
**Status**: Production Ready
**Compatibility**: Claude Desktop 0.6+

**Questions?** Check main BACOWR documentation or GitHub issues.
