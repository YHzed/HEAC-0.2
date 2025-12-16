import re

def parse_cermet_string(raw):
    """Test the parsing logic"""
    # Common Hard Phases
    hard_phases = ['WC', 'TiC', 'Ti(C,N)', 'TiCN', 'TaC', 'NbC', 'Cr3C2', 'VC', 'Mo2C']
    # Common Binder Elements
    binders = ['Co', 'Ni', 'Fe', 'Cr', 'Mo', 'Al', 'V', 'Ti', 'Mn']
    
    current_hard = 'WC' # Default
    hard_amount = 0.0
    binder_comp = {}
    
    # Pre-processing cleanup
    if raw.lower().startswith('b '):
        raw = raw[2:].strip()
        
    # Split by separators (-, space, +)
    tokens = re.split(r'[+\-\s]+', raw)
    
    print(f"\nParsing: '{raw}'")
    print(f"Tokens: {tokens}")
    
    total_binder_wt = 0.0
    
    # Logic: scan tokens
    for i, token in enumerate(tokens):
        if not token: continue
        
        print(f"  Token {i}: '{token}'", end='')
        
        # Check ceramic
        is_ceramic = False
        for hp in hard_phases:
            if hp.lower() == token.lower() or hp.lower() in token.lower():
                current_hard = hp
                is_ceramic = True
                print(f" -> Ceramic: {hp}")
                break
        if is_ceramic: continue
        
        # Check Number
        try:
            val = float(token)
            # Valid number. Check next token for Element?
            if i + 1 < len(tokens):
                next_tok = tokens[i+1]
                if next_tok in binders:
                    # "25 Co" case
                    binder_comp[next_tok] = binder_comp.get(next_tok, 0.0) + val
                    total_binder_wt += val
                    print(f" -> Number: {val}, next is {next_tok}")
                    continue
        except ValueError:
            pass

        # Check Binder+Number combined (10Co)
        match_pre = re.match(r'^(\d+(?:\.\d+)?)([A-Za-z]+)$', token)
        match_post = re.match(r'^([A-Za-z]+)(\d+(?:\.\d+)?)$', token)
        
        if match_pre:
            b_amt = float(match_pre.group(1))
            b_el = match_pre.group(2)
            if b_el in binders:
                binder_comp[b_el] = binder_comp.get(b_el, 0.0) + b_amt
                total_binder_wt += b_amt
                print(f" -> Pre-match: {b_amt} {b_el}")
        elif match_post:
            b_el = match_post.group(1)
            b_amt = float(match_post.group(2))
            if b_el in binders:
                binder_comp[b_el] = binder_comp.get(b_el, 0.0) + b_amt
                total_binder_wt += b_amt
                print(f" -> Post-match: {b_el} {b_amt}")
        else:
            print(f" -> Skipped")
             
    # Calculate Hard Phase Amount if missing
    if hard_amount == 0 and total_binder_wt > 0:
        hard_amount = 100.0 - total_binder_wt
    
    # Normalize Binder
    normalized_binder = {}
    if total_binder_wt > 0:
        normalized_binder = {k: v/total_binder_wt for k, v in binder_comp.items()}
    else:
        normalized_binder = {'Co': 1.0} # Default/Err
        
    print(f"Result: total_binder_wt={total_binder_wt}, binder_comp={binder_comp}")
    print(f"Normalized: {normalized_binder}")
    return normalized_binder

# Test cases from the data
test_cases = [
    "b WC 25 Co",
    "b WC 10 Co",
    "b WC 7 Fe 2 Ni 1 Co",
    "b WC x Co",
    "b WC 8.5 Fe 1.5 Ni"
]

for tc in test_cases:
    result = parse_cermet_string(tc)
    print(f"=> {result}\n")
