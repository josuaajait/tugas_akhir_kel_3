"""Bounded stdout/stderr capture for processes connected to candidate execution."""
import subprocess
import threading


class OutputLimitError(RuntimeError):
    def __init__(self, output, stderr):
        super().__init__('Batas keluaran proses terlampaui.')
        self.output, self.stderr = output, stderr


def bounded_run(args, *, timeout, capture_output=True, shell=False, output_limit=8_000_000):
    if shell or not capture_output or output_limit < 1:
        raise ValueError('Bounded capture membutuhkan shell=False, capture_output=True dan batas positif.')
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    buffers = [bytearray(), bytearray()]
    lock = threading.Lock()
    exceeded = threading.Event()
    used = 0

    def read(stream, index):
        nonlocal used
        try:
            while chunk := stream.read(65536):
                with lock:
                    room = max(0, output_limit-used)
                    buffers[index].extend(chunk[:room])
                    used += min(room, len(chunk))
                    overflow = len(chunk) > room
                if overflow:
                    exceeded.set()
                    try:
                        process.kill()
                    except OSError:
                        pass
                    return
        finally:
            stream.close()

    threads = [threading.Thread(target=read, args=(stream, index), daemon=True)
               for index, stream in enumerate((process.stdout, process.stderr))]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait(timeout=5)
    finally:
        for thread in threads:
            thread.join(timeout=2)
    with lock:
        stdout, stderr = bytes(buffers[0]), bytes(buffers[1])
    if exceeded.is_set():
        raise OutputLimitError(stdout, stderr)
    if timed_out:
        raise subprocess.TimeoutExpired(args, timeout, output=stdout, stderr=stderr)
    if any(t.is_alive() for t in threads):
        raise OutputLimitError(stdout, stderr)
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
