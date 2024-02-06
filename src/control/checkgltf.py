import sys
import json


HELP = """
USAGE
python checkgltf.py --help
python checkgltf.py infile

EFFECT
If --help is present, prints this text and exits.

Checks whether the contents of the infile looks like GLTF content.

PRINTS the string "model/gltf+json" if it is so,
otherwise one or more diagnostics.

RETURNS 0 if the file content is GLTF, otherwise 1.
"""


def check(fileIn):
    good = True
    messages = []

    try:
        with open(fileIn, "r") as fh:
            data = json.load(fh)

            if "asset" not in data:
                messages.append("JSON content has no key 'asset'")
                good = False
            else:
                if "version" not in data["asset"]:
                    messages.append("Asset has no version")
                    good = False

    except Exception:
        messages.append("Content is not JSON")
        good = False

    return (good, messages)


def main():
    args = sys.argv[1:]
    if not args or "--help" in args:
        print(HELP)
        return -1

    if len(args) > 1:
        print(HELP)
        print("Supply exactly one argument")
        return -1

    inFile = args[0]
    (good, messages) = check(inFile)
    if good:
        print("model/gltf+json")
        return 0

    for msg in messages:
        print(msg)
    return 1


if __name__ == "__main__":
    exit(main())
