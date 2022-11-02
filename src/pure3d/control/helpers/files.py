import json
import os
import yaml
import re

from control.helpers.generic import AttrDict


IMAGE_RE = re.compile(r"""^.*\.(png|jpg|jpeg)$""", re.I)


def readPath(filePath, mode="r"):
    if os.path.isfile(filePath):
        with open(filePath, mode) as fh:
            text = fh.read()
        return text
    return ""


def readFile(fileDir, fileName, mode="r"):
    filePath = f"{fileDir}/{fileName}"
    if not os.path.isfile(filePath):
        return f"No file {fileName} in {fileDir}"
    return open(filePath, mode)


def readJson(path):
    if not os.path.isfile(path):
        return None

    data = readPath(path)

    if data:
        return json.loads(data)

    return None


def readYaml(path):
    if not os.path.isfile(path):
        return None
    with open(path) as fh:
        data = yaml.load(fh, Loader=yaml.FullLoader)
    return AttrDict(data)


def dirExists(path):
    return os.path.isdir(path)


def listFiles(path, ext):
    if not os.path.isdir(path):
        return []

    files = []

    nExt = len(ext)
    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if name.endswith(ext) and entry.is_file():
                files.append(name[0:-nExt])

    return files


def listImages(path):
    if not os.path.isdir(path):
        return []

    files = []

    with os.scandir(path) as dh:
        for entry in dh:
            name = entry.name
            if IMAGE_RE.match(name) and entry.is_file():
                files.append(name)

    return files
