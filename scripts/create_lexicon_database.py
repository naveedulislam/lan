#!/usr/bin/env python3
"""
Script to create lexicon.sqlite database from XML files in db/lexica/ara/lan
"""

import re
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET


def load_reference_mappings(reference_file):
    """Load file mappings from reference file"""
    file_mappings = {}
    try:
        with open(reference_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line and 'Pages:' in line and 'File:' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        pages_part = parts[1].strip()
                        file_part = parts[2].strip()
                        
                        # Extract page range
                        page_match = re.search(r'Pages:\s*(\d+)–(\d+)', pages_part)
                        if page_match:
                            start_page = int(page_match.group(1))
                            end_page = int(page_match.group(2))
                        else:
                            start_page = end_page = None
                        
                        # Extract filename
                        file_match = re.search(r'File:\s*(\S+)', file_part)
                        if file_match:
                            filename = file_match.group(1)
                            file_mappings[filename] = {
                                'start_page': start_page,
                                'end_page': end_page
                            }
    except Exception as e:
        print(f"Warning: Could not load reference mappings: {e}")
    
    return file_mappings


def create_database(db_path):
    """Create the SQLite database with the lexicon table"""
    # Remove existing database
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            print(f"Warning: Could not remove existing database {db_path}")
            print("The file may be in use. Trying to continue...")
            # Try to connect anyway - SQLite might be able to handle it
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create entry table
    cursor.execute('''
        CREATE TABLE entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root TEXT,
            word TEXT,
            bword TEXT,                   
            itype TEXT,
            nodeid TEXT,
            xml TEXT,
            file TEXT,
            page INTEGER,
            supplement INTEGER DEFAULT 0
        )
    ''')
    
    # Create lexicon table for file/letter mappings
    cursor.execute('''
        CREATE TABLE lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter TEXT,
            start_page INTEGER,
            end_page INTEGER,
            filename TEXT,
            file_abbrev TEXT,
            is_supplement INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    return conn


def populate_lexicon_table(conn, reference_file):
    """Populate the lexicon table with data from reference file"""
    cursor = conn.cursor()
    
    try:
        with open(reference_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line and 'Pages:' in line and 'File:' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        # Extract letter
                        letter_part = parts[0].strip()
                        letter_match = re.search(r'Arabic Letter:\s*(.+)', letter_part)
                        letter = letter_match.group(1) if letter_match else ''
                        
                        # Extract page range
                        pages_part = parts[1].strip()
                        page_match = re.search(r'Pages:\s*(\d+)–(\d+)', pages_part)
                        start_page = int(page_match.group(1)) if page_match else None
                        end_page = int(page_match.group(2)) if page_match else None
                        
                        # Extract filename
                        file_part = parts[2].strip()
                        file_match = re.search(r'File:\s*(\S+)', file_part)
                        filename = file_match.group(1) if file_match else ''
                        file_abbrev = filename.replace('.xml', '') if filename else ''
                        
                        # Check if supplement
                        is_supplement = 1 if 'Supplement' in line else 0
                        
                        # Insert into lexicon table
                        cursor.execute('''
                            INSERT INTO lexicon (letter, start_page, end_page, filename, file_abbrev, is_supplement)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (letter, start_page, end_page, filename, file_abbrev, is_supplement))
        
        conn.commit()
        print(f"Populated lexicon table with reference data")
        
    except Exception as e:
        print(f"Warning: Could not populate lexicon table: {e}")


def remove_diacritics(text):
    """Remove Arabic diacritics from text to create bword"""
    if not text:
        return text
    
    # Arabic diacritics Unicode ranges
    diacritics = [
        '\u064B',  # Fathatan
        '\u064C',  # Dammatan  
        '\u064D',  # Kasratan
        '\u064E',  # Fatha
        '\u064F',  # Damma
        '\u0650',  # Kasra
        '\u0651',  # Shadda
        '\u0652',  # Sukun
        '\u0653',  # Maddah above
        '\u0654',  # Hamza above
        '\u0655',  # Hamza below
        '\u0656',  # Subscript alef
        '\u0657',  # Inverted damma
        '\u0658',  # Mark noon ghunna
        '\u0659',  # Zwarakay
        '\u065A',  # Vowel sign small v above
        '\u065B',  # Vowel sign inverted small v above
        '\u065C',  # Vowel sign dot below
        '\u065D',  # Reversed damma
        '\u065E',  # Fatha with two dots
        '\u065F',  # Wavy hamza below
        '\u0670',  # Superscript alef
    ]
    
    result = text
    for diacritic in diacritics:
        result = result.replace(diacritic, '')
    
    return result


def extract_page_from_pb(pb_element):
    """Extract page number from pb element"""
    if pb_element is not None and 'n' in pb_element.attrib:
        try:
            return int(pb_element.attrib['n'])
        except ValueError:
            pass
    return None


def get_current_page(element, file_mapping, tree_root):
    """Get the current page number for an element"""
    # Get all elements in document order
    all_elements = list(tree_root.iter())
    
    # Find the position of our element
    element_position = None
    for i, elem in enumerate(all_elements):
        if elem == element:
            element_position = i
            break
    
    if element_position is None:
        # Fallback to start page
        if file_mapping and file_mapping.get('start_page'):
            return file_mapping['start_page']
        return None
    
    # Find all pb elements that come before this element and get the last one
    last_pb_page = None
    for i in range(element_position):
        elem = all_elements[i]
        if elem.tag == 'pb':
            page_num = extract_page_from_pb(elem)
            if page_num is not None:
                last_pb_page = page_num
    
    # If we found a pb element before this element, the entry is on that page
    if last_pb_page is not None:
        return last_pb_page
    
    # If no pb found before this element, it's on the start page
    if file_mapping and file_mapping.get('start_page'):
        return file_mapping['start_page']
    
    return None


def find_root_in_ancestors(element, tree_root):
    """Find root value by looking at the XML structure"""
    # Find all div2 elements with type="root"
    div2_roots = tree_root.findall('.//div2[@type="root"]')
    
    # For each div2 root, check if our element is inside it
    for div2 in div2_roots:
        # Check if the element is a descendant of this div2
        for descendant in div2.iter():
            if descendant == element:
                # Found our element in this div2, get the root text
                head = div2.find('.//head')
                if head is not None:
                    foreign = head.find('.//foreign[@lang="ar"]')
                    if foreign is not None and foreign.text:
                        return foreign.text.strip()
    
    return ''


def process_xml_file(xml_file, conn, file_mappings):
    """Process a single XML file and extract entries"""
    cursor = conn.cursor()
    filename = xml_file.name
    
    # Get file mapping
    file_mapping = file_mappings.get(filename, {})
    
    print(f"Processing {filename}...")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all entryFree elements
        entries = root.findall('.//entryFree')
        
        for entry in entries:
            nodeid = entry.get('id', '')
            key = entry.get('key', '')
            entry_type = entry.get('type', '')
            
            # Extract itype if present
            itype_elem = entry.find('.//itype')
            itype = itype_elem.text.strip() if itype_elem is not None and itype_elem.text else ''
            
            # Determine root and word
            root_value = ''
            word_value = key  # Start with key if it exists
            
            # If no key attribute, try to extract word from orth element
            if not word_value:
                orth_elem = entry.find('.//form/orth[@lang="ar"]')
                if orth_elem is not None and orth_elem.text:
                    word_value = orth_elem.text.strip()
            
            if itype == 'alphabetical letter':
                root_value = key if key else word_value
                word_value = key if key else word_value  # Fix: alphabetical letters should have word = key (same as root)
            else:
                # Look for root in parent div2 elements
                root_value = find_root_in_ancestors(entry, root)
            
            # Get current page
            page = get_current_page(entry, file_mapping, root)
            
            # Create bword (word without diacritics)
            bword_value = remove_diacritics(word_value)
            
            # Convert entry to XML string
            xml_string = ET.tostring(entry, encoding='unicode')
            
            # Get file abbreviation (remove .xml extension)
            file_abbrev = filename.replace('.xml', '')
            
            # Determine supplement value based on filename ending
            supplement_value = 1 if file_abbrev.endswith('1') else 0
            
            # Insert into database
            cursor.execute('''
                INSERT INTO entry (root, word, bword, itype, nodeid, xml, file, page, supplement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (root_value, word_value, bword_value, itype, nodeid, xml_string, file_abbrev, page, supplement_value))
        
        conn.commit()
        print(f"Processed {len(entries)} entries from {filename}")
        
    except ET.ParseError as e:
        print(f"Error parsing {filename}: {e}")
    except Exception as e:
        print(f"Error processing {filename}: {e}")


def create_lexicon_database(xml_dir, db_path, reference_file):
    """Main function to create the lexicon database"""
    print("Creating lexicon database...")
    
    # Load reference mappings
    file_mappings = load_reference_mappings(reference_file)
    print(f"Loaded mappings for {len(file_mappings)} files")
    
    # Create database
    conn = create_database(db_path)
    
    # Populate lexicon table
    populate_lexicon_table(conn, reference_file)
    
    # Process XML files in the order specified in the reference file
    if file_mappings:
        # Process files in reference order
        processed_files = set()
        with open(reference_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line and 'File:' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        file_part = parts[2].strip()
                        file_match = re.search(r'File:\s*(\S+)', file_part)
                        if file_match:
                            filename = file_match.group(1)
                            xml_file = xml_dir / filename
                            if xml_file.exists() and filename not in processed_files:
                                process_xml_file(xml_file, conn, file_mappings)
                                processed_files.add(filename)
        
        # Process any remaining XML files not in reference
        xml_files = sorted(xml_dir.glob('*.xml'))
        xml_files = [f for f in xml_files if not f.name.startswith('__')]  # Skip __contents__.xml
        
        for xml_file in xml_files:
            if xml_file.name not in processed_files:
                print(f"Processing additional file: {xml_file.name}")
                process_xml_file(xml_file, conn, file_mappings)
    else:
        # Fallback: process all XML files
        xml_files = sorted(xml_dir.glob('*.xml'))
        xml_files = [f for f in xml_files if not f.name.startswith('__')]  # Skip __contents__.xml
        
        for xml_file in xml_files:
            process_xml_file(xml_file, conn, file_mappings)
    
    # Get total count
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM entry')
    total_entries = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\nDatabase created successfully!")
    print(f"Total entries: {total_entries}")
    print(f"Database saved to: {db_path}")


def main():
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    xml_dir = project_root / 'db' / 'lexica' / 'ara' / 'lan'
    db_path = project_root / 'lexicon.sqlite'
    reference_file = project_root / 'references' / 'lexicon_refernce_letters.txt'
    
    # Create database
    create_lexicon_database(xml_dir, db_path, reference_file)


if __name__ == '__main__':
    main()
