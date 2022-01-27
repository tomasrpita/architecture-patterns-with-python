import os
import shutil
import hashlib
from pathlib import Path

BLOCKSIZE = 65536


def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()



def read_paths_and_hashes(path):
    hashes = {}
    for folder, _, files in os.walk(path):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes



def sync(source, dest):
    # Imperative shell step 1, gather inputs
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)


    # step 2: call funtional core
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # imperative shell step #3, apply outputs
    for action, *paths in actions:
        if action == "copy":
            shutil.copyfile(*paths)
        if action == "move":
            shutil.move(*paths)
        if action == "delete":
            shutil.remmove(paths[0])
    
        

