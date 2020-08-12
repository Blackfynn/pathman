import os


def is_file(abspath: str) -> bool:
    """Determines if the path is a file

    Parameters
    ----------
    abspath: str
        Path to inspect

    Returns
    -------
    bool: True if inspected path appears to be a file, otherwise False
    """
    # split into path + extension. assume no extension means a directory
    path_segments = os.path.splitext(abspath)
    if path_segments[-1] == "":
        return False
    return True
