# Aorist Correction Change Patterns
**Lane's Arabic-English Lexicon - Systematic Aorist Form Corrections**

## Overview
This document describes the systematic patterns used to correct aorist verb forms in Lane's Lexicon XML files. These patterns can be automated and applied to all alphabet files (ua0.xml, ub0.xml, etc.).

## Problem Description
The original XML contains systematic errors where aorist forms are incorrectly formatted as past tense forms instead of proper aorist (imperfect) forms with the يَ prefix.

## Change Patterns

### Pattern Detection Method
The script analyzes the diacritic on the second radical of existing aorist forms to determine the intended conjugation variety, preserving Harry Diakoff's original linguistic choices.

### Lane's 6 Conjugation Varieties
Based on Lane's table, Arabic verbs follow these patterns:

| Variety | Perfect | Aorist | Description |
|---------|---------|--------|-------------|
| 1 | فَعَلَ | يَفْعُلُ | fatḥa → ḍamma |
| 2 | فَعَلَ | يَفْعِلُ | fatḥa → kasra |
| 3 | فَعَلَ | يَفْعَلُ | fatḥa → fatḥa |
| 4 | فَعِلَ | يَفْعَلُ | kasra → fatḥa |
| 5 | فَعُلَ | يَفْعُلُ | ḍamma → ḍamma |
| 6 | فَعِلَ | يَفْعِلُ | kasra → kasra |

### Diacritic Analysis Logic
```
If second radical has ḍamma (ُ) → يَفْعُلُ pattern (varieties 1,5)
If second radical has fatḥa (َ) → يَفْعَلُ pattern (varieties 3,4)  
If second radical has kasra (ِ) → يَفْعِلُ pattern (varieties 2,6)
```

### XML Transformation Patterns

#### Pattern 1: Standard aorist form
**Regex:** `aor\. \n\s+<form n="infl">\n\s+<orth orig="\w+" lang="ar">([^<]+)</orth></form>`

**Transformation:**
- Extract current incorrect form (e.g., `بَتُرَ`)
- Analyze diacritic on second radical (`ُ`)
- Generate correct aorist (`يَبْتُرُ`)
- Replace in XML structure

#### Pattern 2: Empty orig attribute
**Regex:** `aor\. \n\s+<form n="infl">\n\s+<orth orig="" [^>]*lang="ar">([^<]+)</orth></form>`

**Transformation:** Same logic as Pattern 1

### Specific Transformation Examples

#### يَفْعُلُ Pattern (Varieties 1,5)
```
Input:  بَتُرَ (current incorrect)
Output: يَبْتُرُ (corrected aorist)
Method: ُ diacritic → يَفْعُلُ pattern
```

#### يَفْعَلُ Pattern (Varieties 3,4)
```
Input:  بَتَرَ (current incorrect)
Output: يَبْتَرُ (corrected aorist)
Method: َ diacritic → يَفْعَلُ pattern
```

#### يَفْعِلُ Pattern (Varieties 2,6)
```
Input:  بَلِدَ (current incorrect)
Output: يَبْلِدُ (corrected aorist)
Method: ِ diacritic → يَفْعِلُ pattern
```

## Implementation Algorithm

1. **Find aorist entries** using regex patterns
2. **Extract current form** from XML
3. **Clean and analyze** root letters
4. **Detect diacritic** on second radical
5. **Determine conjugation variety** based on diacritic
6. **Generate correct aorist** using variety rules
7. **Replace in XML** preserving structure

## Quality Assurance

### Validation Rules
- Preserve original root consonants
- Maintain XML structure integrity
- Respect original diacritic choices (Diakoff's linguistics)
- Generate proper يَ prefix for all aorists
- Apply correct vowel patterns per variety

### Statistics Tracking
- Count corrections per pattern type
- Track distribution across varieties
- Measure processing success rate

## Automation for All Alphabets

This pattern can be applied to all alphabet files:
- ua0.xml (Alif letters)
- ub0.xml (Ba letters) ✓ Completed
- ud0.xml (Dal letters)
- uf0.xml (Fa letters)
- [... all other alphabet files]

## File Structure Preservation
- Original files backed up via OneDrive/Git
- In-place modifications for cleaner workflow
- Commit changes after each alphabet for version control

---
**Generated:** September 5, 2025  
**Script:** fix_aorists.py  
**Author:** Automated documentation from aorist correction process
