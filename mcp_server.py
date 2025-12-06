#!/usr/bin/env python3
"""
MCP Server for Kommune Archive Access

This server provides tools and resources to search and access
the downloaded kommune archive data via the Model Context Protocol.
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Kommune Archive Server")

# Base directory for archives (can be overridden via environment variable)
ARCHIVE_BASE_DIR = os.getenv("KOMMUNE_ARCHIVE_DIR", "./archive-*")


def get_available_communes() -> List[str]:
    """Get list of available commune archives."""
    archives = glob.glob(ARCHIVE_BASE_DIR)
    communes = []
    for archive in archives:
        if os.path.isdir(archive):
            commune_name = os.path.basename(archive).replace("archive-", "")
            communes.append(commune_name)
    return sorted(communes)


def search_cases_in_directory(directory: str, search_term: str) -> List[Dict[str, str]]:
    """Search for cases containing the search term in details.txt files."""
    results = []
    search_term_lower = search_term.lower()
    
    for details_file in glob.glob(f"{directory}/**/details.txt", recursive=True):
        try:
            with open(details_file, "r", encoding="utf-8") as f:
                content = f.read()
                if search_term_lower in content.lower():
                    case_dir = os.path.dirname(details_file)
                    case_name = os.path.basename(case_dir)
                    
                    # Extract date from path (format: archive-xxx/YYYY/MM/DD/case)
                    path_parts = case_dir.split(os.sep)
                    if len(path_parts) >= 4:
                        year, month, day = path_parts[-4], path_parts[-3], path_parts[-2]
                        date_str = f"{year}-{month}-{day}"
                    else:
                        date_str = "unknown"
                    
                    # Extract first line (usually contains the main IDs)
                    first_lines = [line for line in content.split("\n") if line.strip()]
                    summary = first_lines[0] if first_lines else case_name
                    
                    results.append({
                        "case_name": case_name,
                        "date": date_str,
                        "path": case_dir,
                        "summary": summary
                    })
        except Exception as e:
            # Skip files that can't be read
            continue
    
    return results


@mcp.tool()
def list_communes() -> List[str]:
    """List all available commune archives.
    
    Returns:
        List of commune names that have been downloaded
    """
    communes = get_available_communes()
    if not communes:
        return ["No commune archives found. Run download.py first to fetch data."]
    return communes


@mcp.tool()
def search_cases(commune: str, search_term: str, max_results: int = 20) -> List[Dict[str, str]]:
    """Search for cases in a commune archive by keyword.
    
    Args:
        commune: Name of the commune (e.g., 'vagan', 'vestvagoy')
        search_term: Keyword to search for in case details
        max_results: Maximum number of results to return (default: 20)
    
    Returns:
        List of matching cases with their metadata
    """
    archive_dir = f"./archive-{commune}"
    
    if not os.path.exists(archive_dir):
        return [{
            "error": f"Archive for commune '{commune}' not found. Available communes: {', '.join(get_available_communes())}"
        }]
    
    results = search_cases_in_directory(archive_dir, search_term)
    
    # Sort by date (newest first) and limit results
    results.sort(key=lambda x: x["date"], reverse=True)
    results = results[:max_results]
    
    if not results:
        return [{
            "message": f"No cases found matching '{search_term}' in {commune} archive"
        }]
    
    return results


@mcp.tool()
def get_case_details(case_path: str) -> Dict[str, any]:
    """Get detailed information about a specific case.
    
    Args:
        case_path: Full path to the case directory
    
    Returns:
        Dictionary with case details and list of documents
    """
    if not os.path.exists(case_path):
        return {"error": f"Case path not found: {case_path}"}
    
    details_file = os.path.join(case_path, "details.txt")
    if not os.path.exists(details_file):
        return {"error": f"details.txt not found in {case_path}"}
    
    try:
        with open(details_file, "r", encoding="utf-8") as f:
            details_content = f.read()
        
        # List all files in the case directory
        files = []
        for file in os.listdir(case_path):
            if file != "details.txt":
                file_path = os.path.join(case_path, file)
                file_size = os.path.getsize(file_path)
                files.append({
                    "name": file,
                    "size_bytes": file_size,
                    "path": file_path
                })
        
        return {
            "path": case_path,
            "details": details_content,
            "documents": files,
            "document_count": len(files)
        }
    except Exception as e:
        return {"error": f"Error reading case details: {str(e)}"}


@mcp.tool()
def list_cases_by_date(commune: str, date: str) -> List[Dict[str, str]]:
    """List all cases for a specific date in a commune archive.
    
    Args:
        commune: Name of the commune (e.g., 'vagan', 'vestvagoy')
        date: Date in YYYY-MM-DD format
    
    Returns:
        List of cases for that date
    """
    archive_dir = f"./archive-{commune}"
    
    if not os.path.exists(archive_dir):
        return [{
            "error": f"Archive for commune '{commune}' not found. Available communes: {', '.join(get_available_communes())}"
        }]
    
    try:
        # Parse date and construct path
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_path = os.path.join(
            archive_dir,
            date_obj.strftime("%Y"),
            date_obj.strftime("%m"),
            date_obj.strftime("%d")
        )
        
        if not os.path.exists(date_path):
            return [{
                "message": f"No cases found for {date} in {commune} archive"
            }]
        
        # List all case directories for this date
        cases = []
        for case_dir in os.listdir(date_path):
            case_full_path = os.path.join(date_path, case_dir)
            if os.path.isdir(case_full_path):
                # Read first line of details for summary
                details_file = os.path.join(case_full_path, "details.txt")
                summary = case_dir
                if os.path.exists(details_file):
                    try:
                        with open(details_file, "r", encoding="utf-8") as f:
                            first_line = f.readline().strip()
                            if first_line:
                                summary = first_line
                    except:
                        pass
                
                cases.append({
                    "case_name": case_dir,
                    "path": case_full_path,
                    "summary": summary
                })
        
        return sorted(cases, key=lambda x: x["case_name"])
        
    except ValueError as e:
        return [{"error": f"Invalid date format. Use YYYY-MM-DD format."}]
    except Exception as e:
        return [{"error": f"Error listing cases: {str(e)}"}]


@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """Read and return a file's content.
    
    Args:
        path: Absolute path to the file
    
    Returns:
        File content as string
    """
    try:
        # Security check: only allow reading from archive directories
        abs_path = os.path.abspath(path)
        if not any(abs_path.startswith(os.path.abspath(f"./archive-{commune}")) 
                   for commune in get_available_communes()):
            return "Error: Access denied. Can only read files from kommune archives."
        
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
