from mcp.server.fastmcp import FastMCP
import os
from datetime import datetime
import subprocess
import markdown2

# Initialize FastMCP server
mcp = FastMCP("notes-saver")

# Constants

RECORDS_DIR = "markdown-notes"  # Directory to save markdown files


def escape_for_applescript(text: str) -> str:
    """Escape special characters for AppleScript."""
    return (text
            .replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\r', ''))


def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML with extra spacing using br tags."""
    # First convert markdown to HTML
    html = markdown2.markdown(markdown_text, extras=[
        "fenced-code-blocks",
        "tables",
        "break-on-newline"
    ])

    # Add extra spacing around headers
    html = (html
            .replace('<h1>', '<br><br><h1>')
            .replace('</h1>', '</h1><br>')
            .replace('<h2>', '<br><br><h2>')
            .replace('</h2>', '</h2><br>')
            .replace('<h3>', '<br><h3>')
            .replace('</h3>', '</h3><br>')
            .replace('<hr>', '<br><hr><br>')
            .replace('</p>', '</p><br>'))

    # Add extra spacing for sections (previously done with CSS)
    html = html.replace('<div class="section"></div>', '<br><br>')

    return html


@mcp.tool()
async def save_to_markdown(content: str, filename: str | None = None) -> str:
    """Save content to a markdown file.

    Args:
        content: The text content to save
        filename: Optional filename (if not provided, uses timestamp)
    """
    # Create records directory if it doesn't exist
    os.makedirs(RECORDS_DIR, exist_ok=True)

    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_record_{timestamp}.md"

    # Ensure filename has .md extension
    if not filename.endswith('.md'):
        filename += '.md'

    # Full path for the file
    filepath = os.path.join(RECORDS_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved to {filepath}"
    except Exception as e:
        return f"Error saving file: {str(e)}"




@mcp.tool()
async def create_note(title: str, content: str, convert_markdown: bool = True) -> str:
    """Create a new note in Apple Notes.

    Args:
        title: The title of the note
        content: The content/body of the note (can be markdown)
        convert_markdown: Whether to convert content from markdown to HTML
    """

    # Convert markdown to HTML if needed
    if convert_markdown:
        content = markdown_to_html(content)

    # Then add the tag (after markdown conversion)
    content_with_tag = f"{content}\n\n#claude"


    # Escape the title and content for AppleScript
    escaped_title = escape_for_applescript(title)
    escaped_content = escape_for_applescript(content_with_tag)

    # Create the AppleScript command
    applescript = f'''
    tell application "Notes"
        tell account "iCloud"
            make new note with properties {{name:"{escaped_title}", body:"{escaped_content}"}}
        end tell
    end tell
    '''

    try:
        result = subprocess.run(['osascript', '-e', applescript],
                              capture_output=True,
                              text=True,
                              check=True)
        return "Note created successfully"
    except subprocess.CalledProcessError as e:
        return f"Error creating note: {e.stderr}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
