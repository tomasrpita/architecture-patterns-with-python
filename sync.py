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


# A function that just does business logic
def determine_actions(source_hashes, dest_hashes, source_folder, dest_folder):
    for sha, filename in source_hashes.items():
        if sha not in dest_hashes:
            sourcepath = Path(source_folder, filename )
            destpath = Path(dest_folder, filename)
            yield "copy", sourcepath, destpath
        elif dest_hashes[sha] != filename:
            olderpath = Path(dest_folder, dest_hashes[sha])
            newestpath = Path(dest_folder, filename)
            yield "move", olderpath, newestpath

    for sha, filename in dest_hashes.items():
        if sha not in source_hashes:
            yield "delete", Path(dest_folder, filename)
        



def sync(reader, filesystem, source_root, dest_root):

    src_hashes = reader(source_root)
    dest_hashes = reader(dest_root)

    for sha, filename in src_hashes.items():
        if sha not in dest_hashes:
            sourcepath = source_root + "/" + filename
            destpath = dest_root + "/" + filename
            filesystem.copy(sourcepath, destpath)

        elif dest_hashes[sha] != filename:
            olddestpath = dest_root + "/" + dest_hashes[sha]
            newdestpath = dest_root + "/" + filename
            filesystem.move(olddestpath, newdestpath)

    for sha, filename in dest_hashes.items():
        if sha not in src_hashes:
            filesystem.delete(dest_root + "/" + filename)
    
        

