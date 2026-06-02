import re

def parse_ghub_lua_to_aimsync(lua_content: str):
    """
    Parses a Logitech G Hub LUA script for recoil movements and converts it
    into AimSync's (x, y, delay_s) pattern format.
    
    Logic:
    - Matches MoveMouseRelative(x, y)
    - Matches Sleep(ms)
    - Pairs them together to create a spray step.
    """
    pattern = []
    
    # regex to find MoveMouseRelative(x, y) - handles integers and floats
    # Updated to strictly match the MoveMouseRelativeFractional format from your script
    move_re = re.compile(r'MoveMouseRelative(?:Fractional)?\(\s*(-?\d+\.?\d*)\s*\*\s*mult\s*,\s*(-?\d+\.?\d*)\s*\*\s*mult\s*\)', re.IGNORECASE)
    # regex to find Sleep(ms)
    sleep_re = re.compile(r'(?:csm|Sleep)\(\s*(\d+)\s*\)', re.IGNORECASE)
    lines = lua_content.splitlines()
    
    current_x, current_y = 0.0, 0.0
    
    for line in lines:
        line = line.strip()
        # Skip comments
        if line.startswith('--') or line.startswith('//'):
            continue
            
        move_match = move_re.search(line)
        if move_match:
            # Accumulate movement until a delay is found
            # We multiply by 1.6 here to convert LUA base (2.0) to AimSync base (1.25)
            current_x += float(move_match.group(1)) * 1.6
            current_y += float(move_match.group(2)) * 1.6
            continue
            
        sleep_match = sleep_re.search(line)
        if sleep_match:
            delay_ms = int(sleep_match.group(1))
            # Add to pattern (rounded for cleanliness) and reset accumulators
            pattern.append((round(current_x, 2), round(current_y, 2), delay_ms / 1000.0))
            current_x, current_y = 0.0, 0.0
            
    return pattern

def generate_python_class_code(game_name: str, weapon_name: str, pattern: list):
    """Utility to generate the code block for a game data file."""
    code = [f"        self.{weapon_name} = ["]
    for x, y, d in pattern:
        code.append(f"            ({x}, {y}, {d}),")
    code.append("        ]")
    return "\n".join(code)