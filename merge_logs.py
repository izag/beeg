import datetime
import os
import time

LOGS = "./logs/"


def merge():
    with open(os.path.join(LOGS, f"all_{int(time.time())}.log"), "w") as out:
        for file in os.listdir(LOGS):
            if not file.startswith('hist_'):
                continue

            full_path = os.path.join(LOGS, file)
            if os.path.getsize(full_path) == 0:
                continue

            mtime = os.path.getmtime(full_path)
            str_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S,%f')

            with open(full_path) as f:
                for line in f.readlines():
                    name = line.strip()
                    print(f'{str_time}\t{name}', file=out)


if __name__ == "__main__":
    merge()
