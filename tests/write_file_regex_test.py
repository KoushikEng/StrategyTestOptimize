import re
import os


def append_ind_to_init(name: str, category: str):
    """
    Append the indicator to the __init__.py file.
    """
    func_name = "calculate_" + name
    init_file = "calculate/indicators/__init__.py"
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write(f"from .{category} import {func_name}\n")
        return

    with open(init_file, "r+") as f:
        content = f.read()

        pattern = rf"^from \.{category} import (.*)$"
        match = re.search(pattern, content, re.MULTILINE)
        
        if not match:
            print("No match found, adding new line")
            f.write(f"\nfrom .{category} import {name}\n")
            return
        
        match_line = match.group()
        print("match: ", match_line)
        existing_func_names = match.group(1).strip()
        print("existing_func_names: ", existing_func_names)

        if func_name in [n.strip() for n in existing_func_names.split(",")]:
            return
        
        replace_line = f"{match_line}, {func_name}"
        print("replace_line: ", replace_line)
        content = re.sub(pattern, replace_line, content, 1, re.MULTILINE)
        print("content: ", content)
        
        f.seek(0)
        f.write(content)
        f.truncate()


if __name__ == "__main__":
    append_ind_to_init("test", "core")
