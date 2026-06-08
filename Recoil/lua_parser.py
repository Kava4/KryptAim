import re

XYD_ENTRY_RE = re.compile(
    r'\{\s*x\s*=\s*(-?\d+(?:\.\d+)?)\s*,\s*y\s*=\s*(-?\d+(?:\.\d+)?)\s*,\s*d\s*=\s*(\d+)\s*\}',
    re.IGNORECASE,
)


def parse_lua_xyd_table(
    lua_content: str,
    *,
    weapon_name: str | None = None,
    mult_base: float = 1.6,
) -> list[tuple[float, float, float]]:
    """Parse G Hub tables like `{ x = 0, y = 1, d = 7 }` into AimSync steps.

    `d` is treated as milliseconds (Sleep delay before/after the move in most scripts).
    `mult_base` matches the 1.6x scale used by other CS2 patterns (G Hub mult ≈ 2.0 parity).
    """
    block = lua_content
    if weapon_name:
        match = re.search(
            rf'{re.escape(weapon_name)}\s*=\s*\{{(.*?)\}}\s*(?:$|\n|\r)',
            lua_content,
            re.S | re.IGNORECASE,
        )
        if match:
            block = match.group(1)

    pattern: list[tuple[float, float, float]] = []
    for x_raw, y_raw, delay_ms in XYD_ENTRY_RE.findall(block):
        x = float(x_raw) * mult_base
        y = float(y_raw) * mult_base
        delay_s = int(delay_ms) / 1000.0
        pattern.append((round(x, 3), round(y, 3), round(delay_s, 4)))
    return pattern


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