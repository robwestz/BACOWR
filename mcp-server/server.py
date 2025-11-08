#!/usr/bin/env python3
"""
BACOWR MCP Server

Model Context Protocol server for BACOWR content generation.
Allows Claude Desktop users to generate backlink content via login instead of API keys.

Usage:
    python server.py
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Add parent directory to path for BACOWR imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.production_api import run_production_job


class BACOWRMCPServer:
    """MCP Server for BACOWR content generation."""

    def __init__(self):
        """Initialize MCP server."""
        self.version = "1.0.0"
        self.tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register available MCP tools."""
        return {
            "generate_backlink_article": {
                "description": "Generate SEO-optimized backlink article with AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "publisher_domain": {
                            "type": "string",
                            "description": "Domain where content will be published (e.g. 'aftonbladet.se')"
                        },
                        "target_url": {
                            "type": "string",
                            "description": "URL to link to (must include protocol)"
                        },
                        "anchor_text": {
                            "type": "string",
                            "description": "Anchor text for the link"
                        },
                        "writing_strategy": {
                            "type": "string",
                            "enum": ["multi_stage", "single_shot"],
                            "description": "Writing strategy: multi_stage (best quality) or single_shot (faster)",
                            "default": "multi_stage"
                        },
                        "country": {
                            "type": "string",
                            "description": "Country code for SERP data (e.g. 'se')",
                            "default": "se"
                        },
                        "use_ahrefs": {
                            "type": "boolean",
                            "description": "Use Ahrefs API for SERP data (requires API key)",
                            "default": False
                        }
                    },
                    "required": ["publisher_domain", "target_url", "anchor_text"]
                }
            },
            "estimate_cost": {
                "description": "Estimate cost for content generation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "writing_strategy": {
                            "type": "string",
                            "enum": ["multi_stage", "single_shot"],
                            "description": "Writing strategy to estimate"
                        },
                        "num_articles": {
                            "type": "integer",
                            "description": "Number of articles to estimate",
                            "default": 1
                        }
                    },
                    "required": ["writing_strategy"]
                }
            },
            "get_provider_info": {
                "description": "Get information about available LLM providers and models",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "0.1.0",
            "serverInfo": {
                "name": "bacowr-mcp-server",
                "version": self.version
            },
            "capabilities": {
                "tools": {}
            }
        }

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request."""
        tools_list = []
        for name, spec in self.tools.items():
            tools_list.append({
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["parameters"]
            })

        return {
            "tools": tools_list
        }

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/call request."""
        if name == "generate_backlink_article":
            return await self._generate_article(arguments)
        elif name == "estimate_cost":
            return await self._estimate_cost(arguments)
        elif name == "get_provider_info":
            return await self._get_provider_info(arguments)
        else:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {name}"
                    }
                ]
            }

    async def _generate_article(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate backlink article using BACOWR."""
        try:
            # Extract parameters
            publisher_domain = args["publisher_domain"]
            target_url = args["target_url"]
            anchor_text = args["anchor_text"]
            writing_strategy = args.get("writing_strategy", "multi_stage")
            country = args.get("country", "se")
            use_ahrefs = args.get("use_ahrefs", False)

            # Run BACOWR in executor (it's synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                run_production_job,
                publisher_domain,
                target_url,
                anchor_text,
                None,  # llm_provider (auto-detect)
                writing_strategy,
                use_ahrefs,
                country,
                None,  # output_dir (use default)
                True   # enable_llm_profiling
            )

            # Format response
            if result['status'] == 'DELIVERED':
                content_parts = [
                    {
                        "type": "text",
                        "text": f"✅ Article generated successfully!\n\n**Status**: {result['status']}\n**Job ID**: {result['job_id']}\n"
                    },
                    {
                        "type": "text",
                        "text": f"\n## Generated Article\n\n{result.get('article', 'No article text available')}"
                    }
                ]

                # Add QC report if available
                if result.get('qc_report'):
                    qc = result['qc_report']
                    qc_text = f"\n## Quality Control Report\n\n"
                    qc_text += f"- **Status**: {qc.get('status', 'N/A')}\n"
                    qc_text += f"- **Issues**: {len(qc.get('issues', []))}\n"

                    if qc.get('issues'):
                        qc_text += f"\n**Issues Found**:\n"
                        for issue in qc['issues'][:3]:  # First 3 issues
                            qc_text += f"- {issue.get('category', 'Unknown')}: {issue.get('message', 'No details')}\n"

                    content_parts.append({
                        "type": "text",
                        "text": qc_text
                    })

                # Add metrics if available
                if result.get('metrics'):
                    metrics = result['metrics']
                    metrics_text = f"\n## Generation Metrics\n\n"
                    if 'generation' in metrics:
                        gen = metrics['generation']
                        metrics_text += f"- **Provider**: {gen.get('provider', 'N/A')}\n"
                        metrics_text += f"- **Model**: {gen.get('model', 'N/A')}\n"
                        metrics_text += f"- **Duration**: {gen.get('duration_seconds', 0):.1f}s\n"
                        metrics_text += f"- **Strategy**: {gen.get('stages_completed', 0)} stages\n"

                    content_parts.append({
                        "type": "text",
                        "text": metrics_text
                    })

                return {
                    "content": content_parts
                }

            elif result['status'] == 'BLOCKED':
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"⚠️ Article generated but blocked by Quality Control.\n\n**Job ID**: {result['job_id']}\n\nPlease review the QC report for details."
                        }
                    ]
                }

            else:  # ABORTED
                error_msg = result.get('error', 'Unknown error occurred')
                return {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"❌ Article generation failed.\n\n**Error**: {error_msg}"
                        }
                    ]
                }

        except Exception as e:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error during generation: {str(e)}"
                    }
                ]
            }

    async def _estimate_cost(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate cost for content generation."""
        try:
            strategy = args["writing_strategy"]
            num_articles = args.get("num_articles", 1)

            # Cost estimates (from cost_calculator.py)
            COST_ESTIMATES = {
                "multi_stage": 0.06,  # Claude Haiku
                "single_shot": 0.02
            }

            TIME_ESTIMATES = {
                "multi_stage": 30,
                "single_shot": 15
            }

            cost_per_article = COST_ESTIMATES.get(strategy, 0.05)
            time_per_article = TIME_ESTIMATES.get(strategy, 20)

            total_cost = cost_per_article * num_articles
            total_time = time_per_article * num_articles

            response_text = f"""
## Cost Estimate

**Strategy**: {strategy}
**Number of articles**: {num_articles}

**Per article**:
- Cost: ${cost_per_article:.2f}
- Time: ~{time_per_article}s

**Total**:
- Cost: ${total_cost:.2f}
- Time: ~{total_time}s ({total_time/60:.1f} minutes)

**Note**: Estimates based on Claude Haiku. Actual costs may vary based on content complexity.
"""

            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }

        except Exception as e:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error estimating cost: {str(e)}"
                    }
                ]
            }

    async def _get_provider_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about available LLM providers."""
        info_text = """
## Available LLM Providers

### Anthropic Claude
- **Models**: Claude 3 Haiku, Claude 3 Sonnet, Claude 3 Opus
- **Default**: Claude 3 Haiku
- **Status**: ✅ Tested and working
- **Best for**: Production content, Swedish language

### OpenAI GPT
- **Models**: GPT-4o, GPT-4o-mini, GPT-4-turbo
- **Default**: GPT-4o-mini
- **Status**: ⚡ Integrated (not yet tested)
- **Best for**: Fast generation, English content

### Google Gemini
- **Models**: Gemini 1.5 Flash, Gemini 1.5 Pro
- **Default**: Gemini 1.5 Flash
- **Status**: ⚡ Integrated (not yet tested)
- **Best for**: Cost-effective generation

## Writing Strategies

### Multi-Stage (Recommended)
- **Quality**: ★★★★★
- **Speed**: Slower (~30-60s)
- **Cost**: Higher (~$0.06/article)
- **Process**: Outline → Content → Polish (3 LLM calls)

### Single-Shot (Fast)
- **Quality**: ★★★★☆
- **Speed**: Faster (~10-20s)
- **Cost**: Lower (~$0.02/article)
- **Process**: One optimized LLM call

## MCP Access Note

When using BACOWR via MCP (Claude Desktop), you're using:
- **Your Claude Desktop subscription** (no additional API costs)
- **Login-based authentication** (no API keys needed)
- **Same quality** as API-key path
- **Privacy**: Data processed through Anthropic
"""

        return {
            "content": [
                {
                    "type": "text",
                    "text": info_text
                }
            ]
        }

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP message."""
        method = message.get("method")
        params = message.get("params", {})

        if method == "initialize":
            return await self.handle_initialize(params)
        elif method == "tools/list":
            return await self.handle_tools_list(params)
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return await self.handle_tool_call(tool_name, arguments)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    async def run(self):
        """Run MCP server (stdio transport)."""
        print("BACOWR MCP Server started", file=sys.stderr)
        print(f"Version: {self.version}", file=sys.stderr)
        print("Waiting for messages on stdin...", file=sys.stderr)

        try:
            while True:
                # Read message from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                try:
                    message = json.loads(line)
                    response = await self.handle_message(message)

                    # Write response to stdout
                    print(json.dumps(response), flush=True)

                except json.JSONDecodeError as e:
                    error_response = {
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)

                except Exception as e:
                    error_response = {
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            print("Server stopped by user", file=sys.stderr)


async def main():
    """Main entry point."""
    server = BACOWRMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
