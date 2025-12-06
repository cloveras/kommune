# Kommune MCP Server

A Model Context Protocol (MCP) server that provides Claude Desktop access to the downloaded kommune (Norwegian municipality) archive data.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that enables AI assistants like Claude to securely connect with local data sources and tools. This MCP server allows Claude Desktop to search and read your downloaded kommune archive files.

## Features

The Kommune MCP Server provides the following tools:

- **list_communes**: List all available commune archives
- **search_cases**: Search for cases by keyword across all dates
- **list_cases_by_date**: List all cases for a specific date
- **get_case_details**: Get detailed information about a specific case
- **read_file**: Read content from archive files (resource)

## Installation

### Prerequisites

- Python 3.10 or higher
- Claude Desktop for Mac (download from [claude.ai](https://claude.ai/download))
- Existing kommune archive data (run `download.py` first to fetch data)

### Step 1: Install Dependencies

If you're using a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

This will install `fastmcp` along with the other dependencies needed for the download script.

### Step 2: Configure Claude Desktop

1. Open Claude Desktop
2. Go to **Settings** → **Developer** → **Edit Config**
3. This will open the `claude_desktop_config.json` file in your default text editor

4. Add the Kommune MCP server configuration to the file:

```json
{
  "mcpServers": {
    "kommune": {
      "command": "python3",
      "args": [
        "/absolute/path/to/kommune/mcp_server.py"
      ],
      "env": {
        "KOMMUNE_ARCHIVE_DIR": "./archive-*"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/kommune/` with the actual absolute path to your kommune repository directory. For example:

```json
{
  "mcpServers": {
    "kommune": {
      "command": "python3",
      "args": [
        "/Users/yourname/projects/kommune/mcp_server.py"
      ]
    }
  }
}
```

If you're using a virtual environment, you can use the Python from your venv:

```json
{
  "mcpServers": {
    "kommune": {
      "command": "/Users/yourname/projects/kommune/venv/bin/python3",
      "args": [
        "/Users/yourname/projects/kommune/mcp_server.py"
      ]
    }
  }
}
```

5. Save the file
6. **Completely quit** Claude Desktop (Cmd+Q, not just closing the window)
7. Restart Claude Desktop

### Step 3: Verify Installation

After restarting Claude Desktop, you should see a small 🔨 (hammer) icon appear in the input area. Click it to see the available tools from the Kommune MCP server.

You can also ask Claude: "What MCP servers are connected?" or "List the available communes"

## Usage Examples

Once configured, you can interact with your kommune archive data through Claude Desktop:

### Basic Commands

- **"List the available communes"**
  - Shows which commune archives you have downloaded

- **"Search for 'Polarsmolt' in vagan commune"**
  - Searches all cases in the Vagan archive for the keyword

- **"Show me all cases from vagan on 2025-01-10"**
  - Lists all cases for a specific date

- **"Get details for case at [path]"**
  - Shows full details and documents for a specific case

### Example Conversation

```
You: List the available communes

Claude: I can see you have archives for these communes:
- vagan
- vestvagoy
- flakstad
- moskenes

You: Search for "byggesak" in vagan from the last week

Claude: I found 5 cases related to "byggesak" in the Vagan archive:
1. 2025-01-10: 25/75 - Gbn 58/28 - Utskifting av oppdrettskar
2. 2025-01-09: 25/63 - Gbn 12/15 - Ny byggesak...
[etc]
```

## Troubleshooting

### Server Not Appearing in Claude Desktop

1. Check that the path in `claude_desktop_config.json` is absolute (starts with `/`)
2. Verify the Python path is correct: `which python3` in terminal
3. Check the Claude Desktop logs:
   - Menu bar: **Claude** → **View Logs**
4. Ensure you completely quit and restarted Claude Desktop (not just closed the window)

### "No commune archives found"

Run the download script first to fetch data:

```bash
python download.py vagan 2024-01-01 2024-12-31
```

### Permission Errors

Make sure the `mcp_server.py` file is executable:

```bash
chmod +x mcp_server.py
```

### Testing the Server Independently

You can test the MCP server without Claude Desktop using the FastMCP CLI:

```bash
# Install FastMCP CLI if not already installed
pip install "fastmcp[cli]"

# Run the server
fastmcp dev mcp_server.py
```

This will start an interactive development server where you can test the tools.

## Configuration Options

### Environment Variables

- `KOMMUNE_ARCHIVE_DIR`: Base directory pattern for archives (default: `./archive-*`)
  
  You can override this in the Claude Desktop config:

  ```json
  {
    "mcpServers": {
      "kommune": {
        "command": "python3",
        "args": ["/path/to/mcp_server.py"],
        "env": {
          "KOMMUNE_ARCHIVE_DIR": "/custom/path/to/archives/archive-*"
        }
      }
    }
  }
  ```

## Security Notes

- The MCP server only provides read access to files in the archive directories
- File reading is restricted to kommune archive folders only
- No write operations are supported
- The server runs locally on your machine; no data is sent to external servers

## Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/mcp)

## License

Same license as the main kommune project (see LICENSE file).
