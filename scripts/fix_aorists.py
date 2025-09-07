#!/usr/bin/env python3
"""
Generic Aorist Correction Script for Lane's Arabic-English Lexicon

REGEX PATTERNS CORRECTED:
========================
This script corrects systematic aorist form errors in Lane's Lexicon XML files.

TARGET PATTERNS:
1. aor. \n\s+<form n="infl">\n\s+<orth orig="\w+" lang="ar">([^<]+)</orth></form>
2. aor. \n\s+<form n="infl">\n\s+<orth orig="" [^>]*lang="ar">([^<]+)</orth></form>

ISSUE DESCRIPTION:
- Harry Diakoff's digitization often contains aorist forms that don't follow standard Arabic patterns
- Instead of proper يَفْعُلُ/يَفْعِلُ/يَفْعَلُ forms, many entries have perfect-like forms (بَتَرَ, بَثُقَ, etc.)
- This script analyzes existing diacritics to determine intended conjugation variety and generates correct aorists

METHODOLOGY:
============
1. DIACRITIC ANALYSIS: Examines current aorist forms to determine intended vowel pattern
2. VARIETY DETECTION: Maps diacritics to Lane's 6 conjugation varieties:
   - Damma (ُ) → يَفْعُلُ pattern (varieties 1,5)
   - Kasra (ِ) → يَفْعِلُ pattern (varieties 2,6) 
   - Fatha (َ) → يَفْعَلُ pattern (varieties 3,4)
3. INTELLIGENT CORRECTION: Preserves linguistic intent rather than imposing single pattern

LANE'S 6 CONJUGATION VARIETIES:
==============================
1. فَعَلَ → يَفْعُلُ
2. فَعَلَ → يَفْعِلُ  
3. فَعَلَ → يَفْعَلُ
4. فَعِلَ → يَفْعَلُ
5. فَعُلَ → يَفْعُلُ
6. فَعِلَ → يَفْعِلُ

USAGE:
======
    python fix_aorists_generic.py <input_file>                    # Generate preview
    python fix_aorists_generic.py <input_file> --apply            # Apply fixes
    python fix_aorists_generic.py ua0.xml                         # Process ua0.xml
    python fix_aorists_generic.py ../db/lexica/ara/lan/ub*.xml    # Process multiple files

EXAMPLE:
========
    Input:  بَتِرَ aor. <form n="infl"><orth orig="Ba" lang="ar">بَتَرَ</orth></form>
    Output: بَتِرَ aor. <form n="infl"><orth orig="Ba" lang="ar">يَبْتَرُ</orth></form>

AUTHOR: GitHub Copilot with Naveed ul Islam
DATE: September 2025
VERSION: 2.0 (Generic/Production)
"""

import re
import sys
import os
import glob
from pathlib import Path
from datetime import datetime

# Arabic diacritics and letter mappings
ARABIC_DIACRITICS = {
    'fatha': '\u064E',      # َ
    'damma': '\u064F',      # ُ
    'kasra': '\u0650',      # ِ
    'sukun': '\u0652',      # ْ
    'shadda': '\u0651',     # ّ
    'tanween_fath': '\u064B',  # ً
    'tanween_damm': '\u064C',  # ٌ
    'tanween_kasr': '\u064D',  # ٍ
}

# Lane's 6 conjugation varieties from his table
LANE_VARIETIES = {
    1: {'perfect': 'فَعَلَ', 'aorist': 'يَفْعُلُ', 'vowel': 'damma'},    # فَعَلَ، يَفْعُلُ
    2: {'perfect': 'فَعَلَ', 'aorist': 'يَفْعِلُ', 'vowel': 'kasra'},    # فَعَلَ، يَفْعِلُ  
    3: {'perfect': 'فَعَلَ', 'aorist': 'يَفْعَلُ', 'vowel': 'fatha'},    # فَعَلَ، يَفْعَلُ
    4: {'perfect': 'فَعِلَ', 'aorist': 'يَفْعَلُ', 'vowel': 'fatha'},    # فَعِلَ، يَفْعَلُ
    5: {'perfect': 'فَعُلَ', 'aorist': 'يَفْعُلُ', 'vowel': 'damma'},    # فَعُلَ، يَفْعُلُ
    6: {'perfect': 'فَعِلَ', 'aorist': 'يَفْعِلُ', 'vowel': 'kasra'},    # فَعِلَ، يَفْعِلُ
}

def remove_diacritics(text):
    """Remove all Arabic diacritics from text."""
    diacritics = ''.join(ARABIC_DIACRITICS.values())
    return ''.join(char for char in text if char not in diacritics)

def get_root_letters(root_text):
    """Extract the basic letters from an Arabic root, removing diacritics."""
    clean_root = remove_diacritics(root_text.strip())
    # Remove any non-Arabic letters
    arabic_letters = ''.join(char for char in clean_root if '\u0600' <= char <= '\u06FF')
    return arabic_letters

def extract_diacritic_from_letter(letter_with_diacritic):
    """Extract the diacritic from a letter, return the diacritic type."""
    if ARABIC_DIACRITICS['fatha'] in letter_with_diacritic:
        return 'fatha'
    elif ARABIC_DIACRITICS['kasra'] in letter_with_diacritic:
        return 'kasra'
    elif ARABIC_DIACRITICS['damma'] in letter_with_diacritic:
        return 'damma'
    elif ARABIC_DIACRITICS['sukun'] in letter_with_diacritic:
        return 'sukun'
    else:
        return None

def analyze_current_aorist_for_intended_pattern(current_aorist):
    """
    Analyze the current aorist form to determine which variety it should follow.
    
    Key insight: The diacritic on the second radical (ع position) in the current
    aorist form indicates Harry Diakoff's intention for which of Lane's 6 varieties 
    should be used.
    
    Returns: vowel type ('damma', 'kasra', 'fatha') for the intended pattern
    """
    if not current_aorist or len(current_aorist) < 4:
        return 'damma'  # Default to variety 1
    
    # Remove يَ prefix if present to get to the root radicals
    clean_aorist = current_aorist
    if clean_aorist.startswith('يَ'):
        clean_aorist = clean_aorist[2:]  # Remove يَ
    
    # Parse the aorist into letters with their diacritics
    letters = []
    current_letter = ""
    for char in clean_aorist:
        if '\u0600' <= char <= '\u06FF' and char not in ARABIC_DIACRITICS.values():
            # This is an Arabic letter (radical)
            if current_letter:
                letters.append(current_letter)
            current_letter = char
        else:
            # This is a diacritic - add to current letter
            current_letter += char
    
    if current_letter:
        letters.append(current_letter)
    
    if len(letters) < 2:
        return 'damma'  # Default
    
    # The key: analyze the second radical's diacritic (corresponds to ع in فعل pattern)
    second_radical_diacritic = extract_diacritic_from_letter(letters[1])
    
    # Map to intended aorist vowel pattern
    if second_radical_diacritic == 'damma':
        return 'damma'  # يَفْعُلُ pattern (varieties 1, 5)
    elif second_radical_diacritic == 'kasra':
        return 'kasra'  # يَفْعِلُ pattern (varieties 2, 6)
    elif second_radical_diacritic == 'fatha':
        return 'fatha'  # يَفْعَلُ pattern (varieties 3, 4)
    else:
        return 'damma'  # Default to most common pattern

def generate_correct_aorist(root_letters, intended_vowel_pattern):
    """
    Generate the correct aorist form using the intended vowel pattern.
    
    Args:
        root_letters: Clean root letters (no diacritics)
        intended_vowel_pattern: 'damma', 'kasra', or 'fatha' for the second radical
    """
    if len(root_letters) < 3:
        return None
    
    # Take first 3 letters for triliteral roots
    first, second, third = root_letters[0], root_letters[1], root_letters[2]
    
    # Determine the vowel for the second radical based on intended pattern
    if intended_vowel_pattern == 'damma':
        second_vowel = ARABIC_DIACRITICS['damma']  # ُ
    elif intended_vowel_pattern == 'kasra':
        second_vowel = ARABIC_DIACRITICS['kasra']  # ِ
    elif intended_vowel_pattern == 'fatha':
        second_vowel = ARABIC_DIACRITICS['fatha']  # َ
    else:
        second_vowel = ARABIC_DIACRITICS['damma']  # Default
    
    # Build the correct aorist: يَفْعُلُ / يَفْعِلُ / يَفْعَلُ pattern
    aorist = (
        'يَ' +                                    # يَ (ya + fatha)
        first + ARABIC_DIACRITICS['sukun'] +     # first letter + sukun
        second + second_vowel +                  # second letter + intended vowel
        third + ARABIC_DIACRITICS['damma']       # third letter + final damma
    )
    
    return aorist

def get_variety_name(vowel_pattern):
    """Get a descriptive name for the vowel pattern."""
    if vowel_pattern == 'damma':
        return 'يَفْعُلُ (varieties 1,5)'
    elif vowel_pattern == 'kasra':
        return 'يَفْعِلُ (varieties 2,6)'
    elif vowel_pattern == 'fatha':
        return 'يَفْعَلُ (varieties 3,4)'
    else:
        return 'unknown'

def find_root_entries_with_diacritic_analysis(xml_content):
    """Find all root entries and analyze their aorist forms with diacritic intelligence."""
    # Pattern to match root sections with their content
    root_pattern = r'<div2 type="root"[^>]*>.*?</div2>'
    root_sections = re.findall(root_pattern, xml_content, re.DOTALL)
    
    entries = []
    for section in root_sections:
        # Extract the root from <head><foreign lang="ar">
        head_match = re.search(r'<head><foreign lang="ar">([^<]+)</foreign></head>', section)
        if head_match:
            root_text = head_match.group(1)
            root_letters = get_root_letters(root_text)
            
            # Find aorist forms in this section - DOCUMENTED REGEX PATTERNS
            # Pattern 1: Standard format with orig attribute
            aorist_pattern1 = r'aor\.\s*\n\s*<form n="infl">\s*\n\s*<orth orig="[^"]*"\s+lang="ar">([^<]*)</orth></form>'
            # Pattern 2: Format with empty orig attribute  
            aorist_pattern2 = r'aor\.\s*\n\s*<form n="infl">\s*\n\s*<orth orig=""\s+[^>]*lang="ar">([^<]*)</orth></form>'
            
            for pattern in [aorist_pattern1, aorist_pattern2]:
                aorist_matches = re.finditer(pattern, section, re.MULTILINE)
                
                for aorist_match in aorist_matches:
                    current_aorist = aorist_match.group(1).strip()
                    
                    # Skip if already in correct يَفْعُلُ format
                    if current_aorist.startswith('يَ'):
                        continue
                    
                    # ENHANCED: Analyze the current aorist to determine the intended pattern
                    intended_vowel_pattern = analyze_current_aorist_for_intended_pattern(current_aorist)
                    
                    # Generate the correct aorist using the detected intended pattern
                    correct_aorist = generate_correct_aorist(root_letters, intended_vowel_pattern)
                    
                    if correct_aorist and current_aorist != correct_aorist:
                        entries.append({
                            'root_text': root_text,
                            'root_letters': root_letters,
                            'current_aorist': current_aorist,
                            'correct_aorist': correct_aorist,
                            'intended_pattern': intended_vowel_pattern,
                            'variety_name': get_variety_name(intended_vowel_pattern),
                            'full_match': aorist_match.group(0)
                        })
    
    return entries

def fix_aorists_in_content(xml_content):
    """Fix all aorist forms in the XML content using diacritic analysis."""
    entries = find_root_entries_with_diacritic_analysis(xml_content)
    
    fixed_content = xml_content
    fixes_made = 0
    
    for entry in entries:
        # Create the replacement pattern
        old_pattern = re.escape(entry['full_match'])
        new_form = entry['full_match'].replace(entry['current_aorist'], entry['correct_aorist'])
        
        # Replace in content
        fixed_content = re.sub(old_pattern, new_form, fixed_content)
        fixes_made += 1
        
        print(f"Root: {entry['root_text']} ({entry['root_letters']})")
        print(f"  Pattern: {entry['variety_name']}")
        print(f"  Fixed: {entry['current_aorist']} -> {entry['correct_aorist']}")
    
    return fixed_content, fixes_made

def generate_preview_report(entries, output_file, input_file):
    """Generate a detailed preview report with diacritic analysis."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("GENERIC AORIST CORRECTION PREVIEW REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Input file: {input_file}\n")
        f.write(f"Total entries to be corrected: {len(entries)}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Script: {os.path.basename(sys.argv[0])}\n\n")
        
        f.write("REGEX PATTERNS CORRECTED:\n")
        f.write("1. aor. \\n\\s+<form n=\"infl\">\\n\\s+<orth orig=\"\\w+\" lang=\"ar\">([^<]+)</orth></form>\n")
        f.write("2. aor. \\n\\s+<form n=\"infl\">\\n\\s+<orth orig=\"\" [^>]*lang=\"ar\">([^<]+)</orth></form>\n\n")
        
        f.write("CORRECTION METHOD:\n")
        f.write("- Analyzes existing diacritics to preserve intended conjugation variety\n")
        f.write("- Uses Harry Diakoff's diacritics to determine correct Lane variety\n")
        f.write("- Respects the original linguistic choices\n\n")
        
        f.write("LANE'S 6 VARIETIES:\n")
        for i, variety in LANE_VARIETIES.items():
            f.write(f"{i}. {variety['perfect']} -> {variety['aorist']}\n")
        f.write("\n")
        
        f.write("FORMAT:\n")
        f.write("Root: [Arabic root] ([clean root letters])\n")
        f.write("  Pattern: [intended variety pattern]\n")
        f.write("  Current: [incorrect aorist]\n")
        f.write("  Correct: [corrected aorist]\n")
        f.write("  Action:  REPLACE\n\n")
        f.write("-" * 50 + "\n\n")
        
        # Group by pattern for better analysis
        pattern_groups = {}
        for entry in entries:
            pattern = entry['intended_pattern']
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(entry)
        
        entry_num = 1
        for pattern, pattern_entries in pattern_groups.items():
            f.write(f"=== {get_variety_name(pattern).upper()} PATTERN ===\n")
            f.write(f"Entries using this pattern: {len(pattern_entries)}\n\n")
            
            for entry in pattern_entries:
                f.write(f"{entry_num:3d}. Root: {entry['root_text']} ({entry['root_letters']})\n")
                f.write(f"     Pattern: {entry['variety_name']}\n")
                f.write(f"     Current: {entry['current_aorist']}\n")
                f.write(f"     Correct: {entry['correct_aorist']}\n")
                f.write(f"     Action:  REPLACE\n")
                f.write(f"     XML Context: ...{entry['full_match'][:50]}...\n")
                f.write("\n")
                entry_num += 1
            
            f.write("\n")
        
        f.write("-" * 50 + "\n")
        f.write(f"SUMMARY: {len(entries)} aorist forms need correction\n")
        f.write(f"Estimated time saved: {len(entries)} minutes = {len(entries)/60:.1f} hours\n\n")
        
        # Pattern statistics
        f.write("PATTERN DISTRIBUTION:\n")
        for pattern, pattern_entries in pattern_groups.items():
            percentage = (len(pattern_entries) / len(entries)) * 100 if entries else 0
            f.write(f"  {get_variety_name(pattern)}: {len(pattern_entries)} ({percentage:.1f}%)\n")
        
        f.write(f"\nTo apply these fixes, run the script with --apply flag:\n")
        f.write(f"python {os.path.basename(sys.argv[0])} {os.path.basename(input_file)} --apply\n")

def process_file(input_file, apply_fixes=False):
    """Process a single XML file."""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist.")
        return False
    
    print(f"Processing: {input_path}")
    print("Using ENHANCED diacritic analysis method")
    
    try:
        # Read the XML file
        with open(input_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Analyze the aorists with enhanced method
        print("Analyzing aorist forms with diacritic intelligence...")
        entries = find_root_entries_with_diacritic_analysis(xml_content)
        
        if not apply_fixes:
            # Generate preview report
            preview_file = input_path.parent / f"aorist_preview_{input_path.stem}.txt"
            print(f"\nGenerating preview report...")
            generate_preview_report(entries, preview_file, input_path)
            print(f"Preview saved to: {preview_file}")
            print(f"Found {len(entries)} aorist forms that need correction.")
            print("\nThis enhanced version preserves Harry Diakoff's intended conjugation varieties!")
            print("\nReview the preview file, then run with --apply to make changes:")
            print(f"python {Path(__file__).name} {input_path.name} --apply")
            
        else:
            # Apply the fixes
            print("Applying enhanced aorist corrections...")
            fixed_content, fixes_made = fix_aorists_in_content(xml_content)
            
            # Apply fixes in-place (OneDrive + Git provide backup)
            with open(input_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"\nCompleted! Made {fixes_made} enhanced fixes.")
            print(f"Corrections applied to: {input_path}")
            print("Original backed up by OneDrive and Git version control")
        
        return True
        
    except Exception as e:
        print(f"Error processing file {input_path}: {e}")
        return False

def main():
    """Main function to process XML files with enhanced diacritic analysis."""
    if len(sys.argv) < 2:
        print("Usage: python fix_aorists_generic.py <input_file> [--apply]")
        print("       python fix_aorists_generic.py ua0.xml")
        print("       python fix_aorists_generic.py ../db/lexica/ara/lan/ub*.xml")
        print("       python fix_aorists_generic.py ub0.xml --apply")
        return 1
    
    # Parse command line arguments
    apply_fixes = "--apply" in sys.argv
    input_files = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    # Expand glob patterns
    all_files = []
    for pattern in input_files:
        if '*' in pattern or '?' in pattern:
            all_files.extend(glob.glob(pattern))
        else:
            all_files.append(pattern)
    
    if not all_files:
        print("Error: No input files specified or found.")
        return 1
    
    print(f"Processing {len(all_files)} file(s)...")
    print(f"Mode: {'APPLY FIXES' if apply_fixes else 'PREVIEW MODE'}")
    print("-" * 50)
    
    success_count = 0
    for file_path in all_files:
        if process_file(file_path, apply_fixes):
            success_count += 1
        print("-" * 50)
    
    print(f"\nProcessing complete: {success_count}/{len(all_files)} files processed successfully.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
