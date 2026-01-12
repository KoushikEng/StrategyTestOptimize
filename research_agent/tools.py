import os


def check_if_path_in_workspace(path):
    """Check if a path is within the workspace directory."""
    print(path, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    return path.startswith(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def write_file(file_path, content, mode='w'):
    """Write content to a file.
    
    Args:
        file_path (str): Path to the file.
        content (str): Content to write to the file.
        mode (str, optional): Mode to open the file in. Defaults to 'w'.
    """
    # if not check_if_path_in_workspace(file_path):
    #     raise ValueError("Path is not within the workspace directory.")
    with open(file_path, mode) as f:
        res = f.write(content)
    return res

def read_file(file_path, mode='r'):
    """Read content from a file.
    
    Args:
        file_path (str): Path to the file.
        mode (str, optional): Mode to open the file in. Defaults to 'r'.
    """
    # if not check_if_path_in_workspace(file_path):
    #     raise ValueError("Path is not within the workspace directory.")
    with open(file_path, mode) as f:
        res = f.read()
    return res