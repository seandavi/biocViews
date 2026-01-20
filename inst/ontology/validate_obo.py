#!/usr/bin/env python3
"""
Validate biocViewsVocab.obo file format and structure.
"""

import re
from collections import defaultdict

def parse_obo(filename):
    """Parse OBO file and return header and terms."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    header = {}
    terms = []
    current_term = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if current_term is not None:
                terms.append(current_term)
                current_term = None
            continue
        
        # Parse header (before first [Term])
        if current_term is None and not line.startswith('[Term]'):
            if ':' in line:
                key, value = line.split(':', 1)
                header[key.strip()] = value.strip()
            continue
        
        # Start new term
        if line.startswith('[Term]'):
            if current_term is not None:
                terms.append(current_term)
            current_term = {
                'id': None,
                'name': None,
                'def': None,
                'is_a': []
            }
            continue
        
        # Parse term fields
        if current_term is not None:
            if line.startswith('id:'):
                current_term['id'] = line.split(':', 1)[1].strip()
            elif line.startswith('name:'):
                current_term['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('def:'):
                current_term['def'] = line.split(':', 1)[1].strip()
            elif line.startswith('is_a:'):
                # Extract parent ID (before the '!')
                is_a_line = line.split(':', 1)[1].strip()
                parent_id = is_a_line.split('!')[0].strip()
                current_term['is_a'].append(parent_id)
    
    # Add last term
    if current_term is not None:
        terms.append(current_term)
    
    return header, terms

def validate_header(header):
    """Validate OBO header."""
    errors = []
    warnings = []
    
    print("Validating header...")
    required_fields = ['format-version', 'ontology']
    for field in required_fields:
        if field not in header:
            errors.append(f"Missing required header field: {field}")
        else:
            print(f"  ✓ {field}: {header[field]}")
    
    return errors, warnings

def validate_terms(terms):
    """Validate term structure."""
    errors = []
    warnings = []
    
    print("\nValidating terms...")
    all_ids = {term['id'] for term in terms}
    
    for i, term in enumerate(terms):
        # Check required fields
        if not term['id']:
            errors.append(f"Term {i+1} missing id")
        if not term['name']:
            errors.append(f"Term {term['id']} missing name")
        
        # Check ID format
        if term['id'] and not re.match(r'^BIOCVIEWS:\d{7}$', term['id']):
            warnings.append(f"Term {term['id']} has non-standard ID format")
        
        # Check is_a relationships reference valid IDs
        for parent_id in term['is_a']:
            if parent_id not in all_ids:
                errors.append(f"Term {term['id']} references non-existent parent: {parent_id}")
    
    return errors, warnings

def check_cycles(terms):
    """Check for cycles in the ontology graph."""
    print("\nChecking for cycles in the ontology...")
    
    # Build adjacency list (child -> parents)
    adjacency = defaultdict(list)
    term_names = {}
    
    for term in terms:
        adjacency[term['id']] = term['is_a']
        term_names[term['id']] = term['name']
    
    # DFS to detect cycles
    visited = set()
    rec_stack = set()
    has_cycle = False
    cycle_path = []
    
    def dfs(node, path=[]):
        nonlocal has_cycle, cycle_path
        
        if has_cycle:
            return
        
        if node in rec_stack:
            has_cycle = True
            cycle_path = path + [node]
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        
        for parent in adjacency.get(node, []):
            dfs(parent, path + [node])
        
        rec_stack.remove(node)
    
    # Check all nodes
    for node in adjacency:
        if node not in visited:
            dfs(node)
    
    if has_cycle:
        print("  ✗ ERROR: Cycle detected in ontology!")
        cycle_repr = ' -> '.join([f'{n} ({term_names.get(n, "?")})' for n in cycle_path])
        print(f"  Cycle path: {cycle_repr}")
        return False
    else:
        print("  ✓ No cycles detected - ontology is a valid DAG")
        return True

def print_summary(header, terms):
    """Print summary statistics."""
    print("\n" + "="*50)
    print("OBO File Summary")
    print("="*50)
    print(f"Format version: {header.get('format-version', 'N/A')}")
    print(f"Ontology: {header.get('ontology', 'N/A')}")
    print(f"Total terms: {len(terms)}")
    
    # Count terms with definitions
    terms_with_def = sum(1 for t in terms if t['def'])
    print(f"Terms with definitions: {terms_with_def}/{len(terms)}")
    
    # Count relationships
    total_relationships = sum(len(t['is_a']) for t in terms)
    print(f"Total is_a relationships: {total_relationships}")
    
    # Find root terms (no parents)
    root_terms = [t for t in terms if not t['is_a']]
    print(f"Root terms: {len(root_terms)}")
    for term in root_terms:
        print(f"  - {term['name']} ({term['id']})")
    
    # Find leaf terms (no children)
    all_parents = set()
    for term in terms:
        all_parents.update(term['is_a'])
    all_ids = {t['id'] for t in terms}
    leaf_ids = all_ids - all_parents
    print(f"Leaf terms: {len(leaf_ids)}")
    
    # Calculate depth distribution
    depths = calculate_depths(terms)
    max_depth = max(depths.values()) if depths else 0
    print(f"Maximum depth: {max_depth}")

def calculate_depths(terms):
    """Calculate depth of each term from root."""
    depths = {}
    
    # Build child -> parent map
    parents_map = {t['id']: t['is_a'] for t in terms}
    
    # BFS from root(s)
    queue = []
    for term in terms:
        if not term['is_a']:
            depths[term['id']] = 0
            queue.append(term['id'])
    
    while queue:
        current = queue.pop(0)
        current_depth = depths[current]
        
        # Find children
        for term in terms:
            if current in term['is_a']:
                if term['id'] not in depths or depths[term['id']] > current_depth + 1:
                    depths[term['id']] = current_depth + 1
                    queue.append(term['id'])
    
    return depths

def main():
    obo_file = 'biocViewsVocab.obo'
    
    print(f"Testing OBO file: {obo_file}\n")
    print("="*50)
    
    try:
        # Parse OBO file
        print("Parsing OBO file...")
        header, terms = parse_obo(obo_file)
        print(f"  ✓ Parsed {len(terms)} terms\n")
        
        # Validate structure
        errors = []
        warnings = []
        
        h_errors, h_warnings = validate_header(header)
        errors.extend(h_errors)
        warnings.extend(h_warnings)
        
        t_errors, t_warnings = validate_terms(terms)
        errors.extend(t_errors)
        warnings.extend(t_warnings)
        
        # Report errors and warnings
        if errors:
            print("\n" + "="*50)
            print("ERRORS")
            print("="*50)
            for error in errors:
                print(f"  ✗ {error}")
        
        if warnings:
            print("\n" + "="*50)
            print("WARNINGS")
            print("="*50)
            for warning in warnings:
                print(f"  ⚠ {warning}")
        
        if not errors and not warnings:
            print("\n  ✓ All validation checks passed!")
        
        # Check for cycles
        is_dag = check_cycles(terms)
        
        # Print summary
        print_summary(header, terms)
        
        # Return status
        print("\n" + "="*50)
        if errors or not is_dag:
            print("VALIDATION FAILED")
            print("="*50)
            return 1
        else:
            print("VALIDATION SUCCESSFUL")
            print("="*50)
            return 0
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
