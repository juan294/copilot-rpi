"""Shared helpers for the Copilot lifecycle runtime tests."""

import importlib.util
import os
from pathlib import Path


LIFECYCLE = Path(__file__).resolve().parents[1] / "templates/scripts/rpi-lifecycle.py"


def load_lifecycle(name="rpi_lifecycle_under_test"):
    """Import the standalone lifecycle runtime from its file path."""
    spec = importlib.util.spec_from_file_location(name, LIFECYCLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def overlay_tree(root):
    """Bytes, link targets, modes and mtimes of a tree, without following links."""
    tree = {}
    for directory, names, files in os.walk(root, followlinks=False):
        for name in names + files:
            path = Path(directory) / name
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                tree[relative] = ("link", os.readlink(path), info.st_mtime_ns)
            elif path.is_dir():
                tree[relative] = ("dir", info.st_mode, info.st_mtime_ns)
            else:
                tree[relative] = ("file", path.read_bytes(), info.st_mode, info.st_mtime_ns)
    return tree
