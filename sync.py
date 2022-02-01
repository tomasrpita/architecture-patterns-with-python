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
        

# A function with  Functional Core, Imperative Shell or FCIS.
# def sync(source, dest):
#     # imperative shell step 1, gather inputs
#     source_hashes = read_paths_and_hashes(source)
#     dest_hashes = read_paths_and_hashes(dest)

#     # step 2: call functional core
#     actions = determine_actions(source_hashes, dest_hashes, source, dest)

#     # imperative shell step 3, apply outputs
#     for action, *paths in actions:
#         if action == "COPY":
#             shutil.copyfile(*paths)
#         if action == "MOVE":
#             shutil.move(*paths)
#         if action == "DELETE":
#             os.remove(paths[0])


# Testing Edge to Edge with Fakes and Dependency Injection
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
    
        

