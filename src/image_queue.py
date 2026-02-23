"""Background image processing queue to avoid blocking request handlers"""
import threading
import queue
import os
from PIL import Image


# Bounded queue prevents memory exhaustion under heavy load
MAX_QUEUE_SIZE = 1000
NUM_WORKERS = 4

_image_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
_worker_threads = []
_started = False
_lock = threading.Lock()


def _process_images():
    """Worker thread that processes image resize tasks from the queue"""
    while True:
        task = _image_queue.get()
        if task is None:
            _image_queue.task_done()
            break
        path, target_size = task
        try:
            if os.path.exists(path):
                with Image.open(path) as img:
                    resized = img.resize(target_size)
                    resized.save(path)
        except Exception:
            pass
        _image_queue.task_done()


def start_worker():
    """Start multiple background image processing worker threads"""
    global _started
    with _lock:
        if _started:
            return
        _started = True
        for _ in range(NUM_WORKERS):
            t = threading.Thread(target=_process_images, daemon=True)
            t.start()
            _worker_threads.append(t)


def queue_resize(path: str, size: tuple = (256, 256)):
    """Queue an image for background resizing. Non-blocking if queue is full."""
    try:
        _image_queue.put_nowait((path, size))
    except queue.Full:
        # Queue full - skip resize, image stays at original size
        pass


def get_queue_depth() -> int:
    """Return current queue depth for monitoring"""
    return _image_queue.qsize()
