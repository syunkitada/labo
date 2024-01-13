import subprocess
import time
import sys
import os


path = os.environ['PATH'] + ":" + sys.path[0]
os.environ['PATH'] = path


def run(*args, **kwargs):
    result = subprocess.run(*args, **kwargs, capture_output=True)
    out = result.stdout.decode('utf-8')+result.stderr.decode('utf-8')
    print("$ " + " ".join(*args))
    if len(out) > 0:
        print(result.stdout.decode('utf-8')+result.stderr.decode('utf-8'))
    return result


def must_run(*args, retry=0, interval=1, **kwargs):
    result = run(*args, **kwargs)
    if result.returncode != 0:
        if retry == 0:
            raise Exception("Failed to run: \n"
                f"return_code={result.check_returncode}\n"
                f"out={result.stdout.decode('utf-8')}\n"
                f"err={result.stderr.decode('utf-8')}")
        time.sleep(interval)
        must_run(*args, **kwargs, retry=retry, interval=interval)
    return result
