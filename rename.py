import os
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    filepath = sys.argv[1]

    with open(filepath, 'r') as f:
        i = 1
        for line in f.readlines():
            url = line.strip()
            if len(url) == 0:
                continue
            slash_pos = url.rfind('/')
            name = url[slash_pos + 1:]
            os.rename(name, f'{i:05}.ts')
            i += 1
