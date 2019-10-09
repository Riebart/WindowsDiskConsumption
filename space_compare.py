#!/usr/bin/env python3

import sys
import csv
import time
import subprocess
from math import ceil
import json

DISK_SIZE = 4096


def try_int(v):
    try:
        return int(v)
    except:
        return v


def try_bool(v):
    if v == "False":
        return False
    elif v == "True":
        return True
    else:
        return None


def container_list(containers, container_name, parent_name=None):
    ret = [{
        "name":
        container_name if parent_name is None else container_name.replace(
            parent_name + "\\", ""),
        "asize":
        0,
        "dsize":
        DISK_SIZE
    }]

    ret += [
        container_list(containers, sub["FullName"], container_name)
        for sub in containers[container_name]["Containers"]
    ]

    ret += [{
        "name": f["FullName"].replace(container_name + "\\", ""),
        "asize": f["Length"],
        "dsize": int(ceil(1.0 * f["Length"] / DISK_SIZE) * DISK_SIZE)
    } for f in containers[container_name]["Files"]]

    ret = [p for p in ret if p is not None]

    return None if len(ret) == 1 else ret


def to_list(files):
    hierarchy = []
    containers = dict()
    for f in files:
        hierarchy.append((f["Parent"], f["FullName"]))
        if f["Parent"] not in containers:
            containers[f["Parent"]] = {"Files": [], "Containers": []}
        if f["IsContainer"]:
            containers[f["FullName"]] = {"Files": [], "Containers": []}
            containers[f["Parent"]]["Containers"].append(f)
        else:
            containers[f["Parent"]]["Files"].append(f)

    # Because tsort doesn't take things with spaces, just map everything to and from numeric IDs
    hierarchy_ids = dict(Forward=dict(), Reverse=dict())
    tsort_input = []
    for h in hierarchy:
        hierarchy_ids["Forward"][h[0]] = hash(h[0])
        hierarchy_ids["Forward"][h[1]] = hash(h[1])
        tsort_input.append((hash(h[0]), hash(h[1])))
    hierarchy_ids["Reverse"] = dict(
        zip(hierarchy_ids["Forward"].values(),
            hierarchy_ids["Forward"].keys()))

    proc = subprocess.Popen(
        ("tsort"), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.stdin.write(("\n".join(["%d %d" % p for p in tsort_input])).encode("utf-8"))
    so, _ = proc.communicate()
    ordering = [
        hierarchy_ids["Reverse"][int(h.strip())]
        for h in so.decode("utf-8").strip().split("\n")
    ]

    # Now, start with the first one, which should be the root of everything.
    # TODO This assumes that everything shares a root
    return [
        1, 0, {
            "progname": "ps_py_space_compare",
            "progver": "0.0.1",
            "timestamp": int(time.time())
        },
        container_list(containers, ordering[0])
    ]


def comm(list1, list2, key):
    # Sort the two lists, to start
    keys1 = set([key(i) for i in list1])
    keys2 = set([key(i) for i in list2])

    keys_ab = keys1.intersection(keys2)
    keys_a = keys1.difference(keys_ab)
    keys_b = keys2.difference(keys_ab)

    lines_a = []
    lines_b = []
    lines_ab = []

    for line in list1:
        if key(line) in keys_a:
            lines_a.append(line)
        elif key(line) in keys_b:
            lines_b.append(line)
        elif key(line) in keys_ab:
            lines_ab.append(line)

    for line in list2:
        if key(line) in keys_a:
            lines_a.append(line)
        elif key(line) in keys_b:
            lines_b.append(line)
        elif key(line) in keys_ab:
            lines_ab.append(line)

    return dict(A=lines_a, B=lines_b, AB=lines_ab)


def drop_duplicates(list, key, merge=lambda v1, v2: v2):
    out = dict()
    for line in list:
        k = key(line)
        if k in out:
            out[k] = merge(out[k], line)
        else:
            out[k] = line
    return sorted(out.values(), key=key)


def get_parent(row):
    if len(row) > 3:
        return row[3] + row[4]
    else:
        return row[0].rsplit("\\", 1)[0]


with open(sys.argv[1], "r") as fp:
    rdr = csv.reader(fp, delimiter='|', quotechar='"')
    file_a = [
        {
            "FullName": row[0],
            "LastWriteTime": row[1],
            "Length": try_int(row[2]),
            # Get the Parent or Directory, if they exist, otherwise split the fullname
            "Parent": get_parent(row),
            "IsContainer": try_bool(row[5]) if len(row) > 5 else False
        } for row in rdr
    ][1:]

if len(sys.argv) > 2:
    with open(sys.argv[2], "r") as fp:
        rdr = csv.reader(fp, delimiter='|', quotechar='"')
        file_b = [
            {
                "FullName": row[0],
                "LastWriteTime": row[1],
                "Length": try_int(row[2]),
                # Get the Parent or Directory, if they exist, otherwise split the fullname
                "Parent": get_parent(row),
                "IsContainer": try_bool(row[5]) if len(row) > 5 else False
            } for row in rdr
        ][1:]
else:
    file_b = file_a
    file_a = []

dirs = [line for line in (file_a + file_b) if line["IsContainer"]]

diff = comm(file_a, file_b, lambda v: v["FullName"])

files_ab = drop_duplicates(diff["AB"] + dirs, lambda v: v["FullName"], lambda a, b: {
    "FullName": a["FullName"],
    "LastWriteTime": a["LastWriteTime"],
    "Length": b["Length"] - a["Length"],
    "OldLength": a["Length"],
    "Parent": a["Parent"],
    "IsContainer": a["IsContainer"]
})

for f in files_ab:
    if f["Length"] != "":
        if f["Length"] < 0:
            f["Length"] *= -1
            diff["A"].append(f)
        elif f["Length"] > 0:
            diff["B"].append(f)

files_a = drop_duplicates(diff["A"] + dirs, lambda v: v["FullName"])
files_b = drop_duplicates(diff["B"] + dirs, lambda v: v["FullName"])
files_c = drop_duplicates(diff["B"] + diff["AB"] + dirs,
                          lambda v: v["FullName"])

if file_a != []:
    with open(
            time.strftime("%FT%T").replace(":", "-") + " Decrease.json",
            "w") as fp:
        fp.write(json.dumps(to_list(files_a), indent=4))

    with open(
            time.strftime("%FT%T").replace(":", "-") + " Increase.json",
            "w") as fp:
        fp.write(json.dumps(to_list(files_b), indent=4))

with open(time.strftime("%FT%T").replace(":", "-") + " Current.json",
          "w") as fp:
    fp.write(json.dumps(to_list(files_c), indent=4))
