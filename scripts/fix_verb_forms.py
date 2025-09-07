#!/usr/bin/env python3
"""
Arabic Verb Form Correction Script for Lane's Arabic-English Lexicon
==================================================================

Based on Lane's "Table of the Conjugations of Arabic Verbs" from the Preface.

ISSUE:
Most verb forms in the digitized version are either incorrect or absent.
Lane provided the patterns in his preface table, but Harry Diakoff's digitization
often contains errors or missing forms.

METHODOLOGY:
1. Extract Arabic roots from div2 sections
2. Find existing verb forms with <itype>N</itype> patterns
3. Generate correct forms based on Lane's 13 standard patterns
4. Apply phonological rules for special cases

LANE'S VERB FORMS:
1. فَعَلَ (Form I - handled by fix_aorists.py)
2. فَعَّلَ (Form II - intensification)
3. فَاعَلَ (Form III - reciprocal/associative)
4. أَفْعَلَ (Form IV - causative)
5. تَفَعَّلَ (Form V - reflexive of II)
6. تَفَاعَلَ (Form VI - reflexive of III)
7. اِنْفَعَلَ (Form VII - passive)
8. اِفْتَعَلَ (Form VIII - middle voice)
9. اِفْعَلَّ (Form IX - colors/defects)
10. اِسْتَفْعَلَ (Form X - seeking/requesting)
11. اِفْعَالَّ (Form XI - rare)
12. اِفْعَوْعَلَ (Form XII - rare)
13. اِفْعَوَّلَ (Form XIII - rare)

REGEX PATTERNS:
Target: <itype>\\d+</itype>\\s*\\n\\s*<orth lang="ar">[^<]+</orth></form>

USAGE:
    python fix_verb_forms.py <input_file>                    # Generate preview
    python fix_verb_forms.py <input_file> --apply            # Apply fixes
    python fix_verb_forms.py ub0.xml                         # Process ub0.xml -> verb_form_preview_ba.txt

"""

import re
import sys
import os
from pathlib import Path
from datetime import datetime

# Arabic diacritics
ARABIC_DIACRITICS = {
    'fatha': '\u064E',      # َ
    'damma': '\u064F',      # ُ
    'kasra': '\u0650',      # ِ
    'sukun': '\u0652',      # ْ
    'shadda': '\u0651',     # ّ
    'tanween_fath': '\u064B',  # ً
    'tanween_damm': '\u064C',  # ٌ
    'tanween_kasr': '\u064D',  # ٍ
    'hamza_above': '\u0654', # ٔ
    'hamza_below': '\u0655', # ٕ
}

# Lane's verb form patterns based on his preface table
VERB_FORMS = {
    # Form I is handled by fix_aorists.py (6 varieties)
    2: {
        'name': 'فَعَّلَ',
        'pattern': 'فَعَّلَ',
        'description': 'Form II - Intensification/Causative'
    },
    3: {
        'name': 'فَاعَلَ', 
        'pattern': 'فَاعَلَ',
        'description': 'Form III - Reciprocal/Associative'
    },
    4: {
        'name': 'أَفْعَلَ',
        'pattern': 'أَفْعَلَ', 
        'description': 'Form IV - Causative'
    },
    5: {
        'name': 'تَفَعَّلَ',
        'pattern': 'تَفَعَّلَ',
        'description': 'Form V - Reflexive of Form II'
    },
    6: {
        'name': 'تَفَاعَلَ',
        'pattern': 'تَفَاعَلَ',
        'description': 'Form VI - Reflexive of Form III'  
    },
    7: {
        'name': 'اِنْفَعَلَ',
        'pattern': 'اِنْفَعَلَ',
        'description': 'Form VII - Passive'
    },
    8: {
        'name': 'اِفْتَعَلَ', 
        'pattern': 'اِفْتَعَلَ',
        'description': 'Form VIII - Middle Voice'
    },
    9: {
        'name': 'اِفْعَلَّ',
        'pattern': 'اِفْعَلَّ', 
        'description': 'Form IX - Colors/Physical Defects'
    },
    10: {
        'name': 'اِسْتَفْعَلَ',
        'pattern': 'اِسْتَفْعَلَ',
        'description': 'Form X - Seeking/Requesting'
    },
    11: {
        'name': 'اِفْعَالَّ',
        'pattern': 'اِفْعَالَّ',
        'description': 'Form XI - Rare pattern'
    },
    12: {
        'name': 'اِفْعَوْعَلَ',
        'pattern': 'اِفْعَوْعَلَ', 
        'description': 'Form XII - Rare pattern'
    },
    13: {
        'name': 'اِفْعَوَّلَ',
        'pattern': 'اِفْعَوَّلَ',
        'description': 'Form XIII - Rare pattern'
    }
}

def remove_diacritics(text):
    """Remove all Arabic diacritics from text.""" 
    diacritics = ''.join(ARABIC_DIACRITICS.values())
    return ''.join(char for char in text if char not in diacritics)

def get_root_letters(root_text):
    """Extract the basic root letters, removing diacritics."""
    clean_root = remove_diacritics(root_text.strip())
    # Keep only Arabic letters
    arabic_letters = ''.join(char for char in clean_root if '\u0600' <= char <= '\u06FF')
    return arabic_letters

def apply_assimilation_rules(form_num, root_letters):
    """
    Apply Lane's phonological assimilation rules for specific verb forms.
    Based on his detailed notes in the preface.
    """
    if len(root_letters) < 3:
        return root_letters
    
    f, a, l = root_letters[0], root_letters[1], root_letters[2]  # ف ع ل
    
    # Form V and VI: اِفَّعَّلَ variations
    if form_num in [5, 6]:
        # When ف is ت، ث، ج، د، ذ، ز، س، ش، ص، ض، ط، ظ
        assimilating_letters = ['ت', 'ث', 'ج', 'د', 'ذ', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ']
        if f in assimilating_letters:
            # Use اِفَّعَّلَ pattern instead of تَفَعَّلَ
            return f + a + l  # Will be handled in generate_verb_form
    
    # Form VII: اِنْفَعَلَ variations
    if form_num == 7:
        # اِنَّصَرَ (for اِنْنَصَرَ) when ف is ن
        if f == 'ن':
            return 'ن' + a + l
        # اِمَّلَسَ (for اِنْمَلَسَ) when ف is م  
        if f == 'م':
            return 'م' + a + l
    
    # Form VIII: اِفْتَعَلَ has many variations
    if form_num == 8:
        # Complex assimilation rules for Form VIII
        if f == 'ت':  # اِتَّبَعَ (for اِتْتَبَعَ)
            return f + a + l
        elif f in ['ث', 'ج', 'د', 'ذ', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ']:
            # Various assimilation patterns documented by Lane
            return f + a + l
    
    return root_letters

def generate_verb_form(form_num, root_letters):
    """
    Generate the correct Arabic verb form based on Lane's patterns.
    """
    if form_num not in VERB_FORMS or len(root_letters) < 3:
        return None
    
    # Apply assimilation rules first
    adjusted_root = apply_assimilation_rules(form_num, root_letters)
    f, a, l = adjusted_root[0], adjusted_root[1], adjusted_root[2]  # فعل
    
    # Generate forms based on Lane's patterns with proper diacritics
    if form_num == 2:  # فَعَّلَ
        return f + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha']
    
    elif form_num == 3:  # فَاعَلَ
        return (f + ARABIC_DIACRITICS['fatha'] + 'ا' + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 4:  # أَفْعَلَ
        return ('أ' + ARABIC_DIACRITICS['fatha'] + f + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 5:  # تَفَعَّلَ
        # Check for assimilation
        if apply_assimilation_rules(5, root_letters) != root_letters:
            # Use اِفَّعَّلَ pattern 
            return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
        else:
            return ('ت' + ARABIC_DIACRITICS['fatha'] + f + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 6:  # تَفَاعَلَ
        # Check for assimilation similar to Form V
        if apply_assimilation_rules(6, root_letters) != root_letters:
            return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + 'ا' + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
        else:
            return ('ت' + ARABIC_DIACRITICS['fatha'] + f + ARABIC_DIACRITICS['fatha'] + 'ا' + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 7:  # اِنْفَعَلَ
        # Handle assimilation cases
        if f == 'ن':  # اِنَّصَرَ pattern
            return ('ا' + ARABIC_DIACRITICS['kasra'] + 'ن' + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
        elif f == 'م':  # اِمَّلَسَ pattern  
            return ('ا' + ARABIC_DIACRITICS['kasra'] + 'م' + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
        else:
            return ('ا' + ARABIC_DIACRITICS['kasra'] + 'ن' + ARABIC_DIACRITICS['sukun'] + f + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 8:  # اِفْتَعَلَ
        return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['sukun'] + 'ت' + ARABIC_DIACRITICS['fatha'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 9:  # اِفْعَلَّ
        return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 10:  # اِسْتَفْعَلَ
        return ('ا' + ARABIC_DIACRITICS['kasra'] + 'س' + ARABIC_DIACRITICS['sukun'] + 'ت' + ARABIC_DIACRITICS['fatha'] + f + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 11:  # اِفْعَالَّ
        return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + 'ا' + l + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 12:  # اِفْعَوْعَلَ
        return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + 'و' + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    elif form_num == 13:  # اِفْعَوَّلَ
        return ('ا' + ARABIC_DIACRITICS['kasra'] + f + ARABIC_DIACRITICS['sukun'] + a + ARABIC_DIACRITICS['fatha'] + 'و' + ARABIC_DIACRITICS['shadda'] + ARABIC_DIACRITICS['fatha'] + l + ARABIC_DIACRITICS['fatha'])
    
    return None

def find_verb_form_entries(xml_content):
    """Find all verb form entries that need correction."""
    # Pattern to match root sections
    root_pattern = r'<div2 type="root"[^>]*>.*?</div2>'
    root_sections = re.findall(root_pattern, xml_content, re.DOTALL)
    
    entries = []
    for section in root_sections:
        # Extract root from <head><foreign lang="ar">
        head_match = re.search(r'<head><foreign lang="ar">([^<]+)</foreign></head>', section)
        if not head_match:
            continue
            
        root_text = head_match.group(1)
        root_letters = get_root_letters(root_text)
        
        if len(root_letters) < 3:
            continue
        
        # Find verb forms: <itype>N</itype> followed by <orth lang="ar">
        verb_pattern = r'<itype>(\d+)</itype>\s*\n\s*<orth lang="ar">([^<]+)</orth></form>'
        verb_matches = re.finditer(verb_pattern, section, re.MULTILINE)
        
        for verb_match in verb_matches:
            form_num = int(verb_match.group(1))
            current_form = verb_match.group(2).strip()
            
            # Skip Form I (handled by fix_aorists.py)
            if form_num == 1:
                continue
                
            # Generate correct form
            correct_form = generate_verb_form(form_num, root_letters)
            
            if correct_form and current_form != correct_form:
                entries.append({
                    'root_text': root_text,
                    'root_letters': root_letters,
                    'form_number': form_num,
                    'form_name': VERB_FORMS.get(form_num, {}).get('name', f'Form {form_num}'),
                    'form_description': VERB_FORMS.get(form_num, {}).get('description', 'Unknown'),
                    'current_form': current_form,
                    'correct_form': correct_form,
                    'full_match': verb_match.group(0)
                })
    
    return entries

def generate_preview_report(entries, output_file, input_file):
    """Generate detailed preview report."""
    # Determine suffix from input file
    input_path = Path(input_file)
    if input_path.stem.startswith('u') and len(input_path.stem) == 3:
        suffix = input_path.stem[1:3]  # e.g., "b0" from "ub0"
    else:
        suffix = input_path.stem
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ARABIC VERB FORM CORRECTION PREVIEW REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Input file: {input_file}\n")
        f.write(f"Total verb forms to be corrected: {len(entries)}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Script: {os.path.basename(sys.argv[0])}\n\n")
        
        f.write("BASED ON LANE'S CONJUGATION TABLE:\n")
        f.write("Forms 2-13 from 'Table of the Conjugations of Arabic Verbs'\n")
        f.write("Form 1 (6 varieties) handled by fix_aorists.py\n\n")
        
        f.write("REGEX PATTERN CORRECTED:\n")
        f.write("<itype>\\d+</itype>\\s*\\n\\s*<orth lang=\"ar\">[^<]+</orth></form>\n\n")
        
        f.write("VERB FORMS COVERED:\n")
        for form_num in range(2, 14):
            if form_num in VERB_FORMS:
                f.write(f"{form_num:2d}. {VERB_FORMS[form_num]['name']} - {VERB_FORMS[form_num]['description']}\n")
        f.write("\n")
        
        f.write("-" * 50 + "\n\n")
        
        # Group by form number
        form_groups = {}
        for entry in entries:
            form_num = entry['form_number']
            if form_num not in form_groups:
                form_groups[form_num] = []
            form_groups[form_num].append(entry)
        
        entry_num = 1
        for form_num in sorted(form_groups.keys()):
            form_entries = form_groups[form_num]
            f.write(f"=== FORM {form_num}: {VERB_FORMS.get(form_num, {}).get('name', 'Unknown')} ===\n")
            f.write(f"Pattern: {VERB_FORMS.get(form_num, {}).get('pattern', 'Unknown')}\n")
            f.write(f"Description: {VERB_FORMS.get(form_num, {}).get('description', 'Unknown')}\n")
            f.write(f"Entries to correct: {len(form_entries)}\n\n")
            
            for entry in form_entries:
                f.write(f"{entry_num:3d}. Root: {entry['root_text']} ({entry['root_letters']})\n")
                f.write(f"     Form: {entry['form_number']} ({entry['form_name']})\n")
                f.write(f"     Current: {entry['current_form']}\n")
                f.write(f"     Correct: {entry['correct_form']}\n")
                f.write(f"     Action:  REPLACE\n")
                f.write(f"     Context: {entry['full_match'][:60]}...\n")
                f.write("\n")
                entry_num += 1
            f.write("\n")
        
        f.write("-" * 50 + "\n")
        f.write(f"SUMMARY: {len(entries)} verb forms need correction\n")
        f.write(f"Estimated time saved: {len(entries)} minutes\n\n")
        
        # Form distribution
        f.write("FORM DISTRIBUTION:\n")
        for form_num in sorted(form_groups.keys()):
            count = len(form_groups[form_num])
            percentage = (count / len(entries)) * 100 if entries else 0
            f.write(f"  Form {form_num:2d}: {count:3d} ({percentage:5.1f}%)\n")
        
        f.write(f"\nTo apply these fixes, run:\n")
        f.write(f"python {os.path.basename(sys.argv[0])} {os.path.basename(input_file)} --apply\n")

def apply_verb_form_fixes(xml_content, entries):
    """Apply verb form corrections to XML content."""
    fixed_content = xml_content
    fixes_made = 0
    
    for entry in entries:
        # Create replacement
        old_pattern = re.escape(entry['full_match'])
        new_form = entry['full_match'].replace(entry['current_form'], entry['correct_form'])
        
        # Apply replacement
        fixed_content = re.sub(old_pattern, new_form, fixed_content)
        fixes_made += 1
        
        print(f"Form {entry['form_number']}: {entry['root_text']} ({entry['root_letters']})")
        print(f"  Fixed: {entry['current_form']} -> {entry['correct_form']}")
    
    return fixed_content, fixes_made

def process_file(input_file, apply_fixes=False):
    """Process a single XML file."""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist.")
        return False
    
    print(f"Processing: {input_path}")
    
    try:
        # Read XML file
        with open(input_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Find verb form entries
        entries = find_verb_form_entries(xml_content)
        
        if not apply_fixes:
            # Generate preview
            # Create suffix for preview file
            if input_path.stem.startswith('u') and len(input_path.stem) == 3:
                suffix = input_path.stem[1:3]  # e.g., "b0" from "ub0"  
            else:
                suffix = input_path.stem
                
            preview_file = Path("references") / f"verb_form_preview_{suffix}.txt"
            
            # Ensure references directory exists
            preview_file.parent.mkdir(exist_ok=True)
            
            generate_preview_report(entries, preview_file, input_path)
            print(f"Preview saved to: {preview_file}")
            print(f"Found {len(entries)} verb forms that need correction.")
            print(f"\nReview the preview file, then run with --apply to make changes:")
            print(f"python {Path(__file__).name} {input_path.name} --apply")
            
        else:
            # Apply fixes
            print("Applying verb form corrections...")
            fixed_content, fixes_made = apply_verb_form_fixes(xml_content, entries)
            
            # Write back to file (OneDrive + Git provide backup)
            with open(input_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"\nCompleted! Made {fixes_made} verb form corrections.")
            print(f"Corrections applied to: {input_path}")
            print("Original backed up by OneDrive and Git version control")
        
        return True
        
    except Exception as e:
        print(f"Error processing file {input_path}: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_verb_forms.py <input_file> [--apply]")
        print("       python fix_verb_forms.py ub0.xml")
        print("       python fix_verb_forms.py ub0.xml --apply")
        return 1
    
    apply_fixes = "--apply" in sys.argv
    input_file = sys.argv[1]
    
    print("Arabic Verb Form Correction Script")
    print("Based on Lane's Conjugation Table")
    print("=" * 50)
    print(f"File: {input_file}")
    print(f"Mode: {'APPLY FIXES' if apply_fixes else 'PREVIEW ONLY'}")
    print()
    
    success = process_file(input_file, apply_fixes)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
