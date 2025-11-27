"""
Script to prepare simplified JSON file for manual sentiment and emotion coding.
Extracts only $oid and text fields from the source JSON file.
"""
import json
from pathlib import Path

# Paths
SOURCE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "1_main.27.11_all-fn.json"
OUTPUT_FILE = Path(__file__).parent / "data_to_code.json"

def prepare_coding_data():
    """Extract $oid and text fields from source JSON."""
    print(f"Reading source file: {SOURCE_FILE}")
    
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract only needed fields
    simplified_data = []
    for item in data:
        simplified_item = {
            "$oid": item["_id"]["$oid"],
            "text": item["text"]
        }
        simplified_data.append(simplified_item)
    
    # Save simplified data
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(simplified_data, f, ensure_ascii=False, indent=2)
    
    print(f"Created simplified file with {len(simplified_data)} elements: {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_coding_data()
