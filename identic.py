# EGE CAN KAYA
# 2018400018

import argparse
import os
import hashlib
from collections import defaultdict

# define a class that will hold the name, path and size of a file
class File:
    def __init__(self, name, path, size):
        self.name = name
        self.path = path
        self.size = size


# define a class that will hold the name and path of a file and also calculate its size
# (sum of the sizes of its files and subdirectories)
class Directory:
    size = 0

    # recursively calculates the size of a directory, making use of os.walk
    def directory_size(self, fullpath):
        totalsize = 0        
        for root, dirs, files in os.walk(fullpath):
            for f in files:
                f_fullpath =  os.path.join(root, f)
                totalsize += os.stat(f_fullpath).st_size
            for d in dirs:
                d_fullpath = os.path.join(root, d)
                totalsize += self.directory_size(d_fullpath)
        return totalsize

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.size = self.directory_size(path) # calculate and save the size of the directory on instantiation

# define a class that will hold the duplicate file text-blocks and the size of the
# duplicate files (for the -s flag)
class Block:
    def __init__(self, block, size):
        self.block = block
        self.size = size

# use argparse to declare what kind of an input is acceptable
ap = argparse.ArgumentParser()
group1 = ap.add_mutually_exclusive_group()
group1.add_argument("-f", action="store_true")
group1.add_argument("-d", action="store_true")
group2 = ap.add_mutually_exclusive_group()
group2.add_argument("-c", action="store_true")
group2.add_argument("-n", action="store_true")
group2.add_argument("-cn", action="store_true")
ap.add_argument("-s", action="store_true")
ap.add_argument("dirs", nargs="*")

# parse the given commandline arguments and set the defaults if needed
args = ap.parse_args()
if not args.f and not args.d:
    args.f = True
if not args.c and not args.n and not args.cn:
    args.c = True

# the directories given in the commandline
d = args.dirs

# containers for all the files and directories
allfiles = []
alldirs = []

# if no directory is given, use the current working directory
if not d:
    d.append(os.getcwd())

# turn all possible relative paths into absolute paths
for i in range(len(d)):
    if not os.path.isabs(d[i]):
        d[i] = os.path.abspath(d[i])

# get all of the files and subdirectories in the given directories, create according File
# and Directory objects from them and place those objects in their respective containers
for entry in d:
    for root, dirs, files in os.walk(entry):
        for x in dirs:
            fullpath = os.path.join(root, x)
            newdir = Directory(x, fullpath)
            alldirs.append(newdir)
        for f in files:
            fullpath =  os.path.join(root, f)
            allfiles.append(File(f, fullpath, os.stat(fullpath).st_size))

# a dictionary where the keys are sha256 hashes and the values are File or Directory objects
hashed_elems = defaultdict(list)

# if -f flag is present
if args.f:
    # for each file, read the contents, hash it using sha256 and map it to the dictionary
    if args.c:
        for curfile in allfiles:
            with open(curfile.path, "rb") as readfile:
                byts = readfile.read()
                hsh = hashlib.sha256(byts).hexdigest()
            hashed_elems[hsh].append(curfile)
    # for each file, hash the name of the file using sha256 and map it to the dictionary
    elif args.n:
        for curfile in allfiles:
           hashed_elems[curfile.name].append(curfile)
    # for each file, read the contents, add the name of the file to the end of the contents, then hash it 
    # and map it to the dictionary
    elif args.cn:
        for curfile in allfiles:
            with open(curfile.path, "rb") as readfile:
                byts = readfile.read() + curfile.name.encode("utf-8")
                hsh = hashlib.sha256(byts).hexdigest()
            hashed_elems[hsh].append(curfile)

# a function which will get a hash for a given directory
def hash_directory(direc_path):
    # if the directory is empty, it gets the hash for the empty string
    if not os.listdir(direc_path):
        return hashlib.sha256("".encode("utf-8")).hexdigest()
    # container which will hold the hashes of all the files and subdirectories
    sub_hashes = []
    # relative paths of the contents of the directory
    subs = os.listdir(direc_path)
    # full paths of the contents of the directory, fill it using the path of the root
    subs_full = [""] * len(subs)
    for i in range(len(subs)):
        subs_full[i] = os.path.join(direc_path, subs[i])
    # for each element, hash the contents and the name and add it to the sub_hashes list
    for i in range(len(subs_full)):
        # if the current element is a file, hash it as if -f -cn flags are given
        if os.path.isfile(subs_full[i]):
            with open(subs_full[i], "rb") as readfile:
                byts = readfile.read()
                hsh = hashlib.sha256(byts).hexdigest()
            sub_hashes.append(hsh)
        # if the current element is a directory, call the hash_directory function to hash it
        if os.path.isdir(subs_full[i]):
            sub_hashes.append(hash_directory(subs_full[i]))
    # sort the sub_hashes list alphabetically, turn it into a string, then hash it to get the 
    # directory's hash
    sub_hashes.sort()
    string = ""
    for h in sub_hashes:
        string += h
    return hashlib.sha256(string.encode("utf-8")).hexdigest()

# if -d flag is present
if args.d:
    if args.c:
        # hash the directories using the hash_directory function and map them to the dictionary
        for curdir in alldirs:
            hsh = hash_directory(curdir.path)
            hashed_elems[hsh].append(curdir)
    elif args.n:
        # hash the directories by their names and map them to the dictionary
        for curdir in alldirs:
            hsh0 = hash_directory(curdir.path)
            hsh1 = hashlib.sha256(curdir.name.encode("utf-8")).hexdigest()
            string = hsh0 + hsh1
            hsh = hashlib.sha256(string.encode("utf-8")).hexdigest()
            hashed_elems[hsh].append(curdir)
    elif args.cn:
        for curdir in alldirs:
            # hash the directories by hash_directory, then concatenate the name of the directory to
            # the end of the first hash, then take another hash. finally, map them to the dictionary
            hsha = hash_directory(curdir.path)
            hsh1 = hashlib.sha256(curdir.name.encode("utf-8")).hexdigest()
            string = hsha + hsh1
            hshb = hashlib.sha256(string.encode("utf-8")).hexdigest()
            hsh = hashlib.sha256((hsha + hshb).encode()).hexdigest()
            hashed_elems[hsh].append(curdir)

# printer portion of the code. check all hashed elements and see if there are some
# who are mapped to the same hash keys, meaning duplicate files/directories
blocks = []
for k, v in hashed_elems.items():
    # same hash for multiple files/directories
    if len(v) > 1:
        v.sort(key = lambda x: x.path)
        block = ""
        lastsize = -1
        for f in v:
            # if -s flag is present and -n flag is not, need to print \t and size of the file/directory
            if args.s and not args.n:
                block += f.path + "\t" + "%d" % f.size + "\n"
            else:
                block += f.path + "\n"
            lastsize = f.size
        # put all of the text blocks in a list of blocks
        blocks.append(Block(block, lastsize))
# if -s is present, sort the blocks by size
if args.s and not args.n:
    blocks.sort(key = lambda x: x.size, reverse = True)
# otherwise, sort them alphabetically
else:    
    blocks.sort(key = lambda x: x.block)
# finally, print all of the blocks to the output stream
for ele in blocks:
    print(ele.block)