"""Background image processing queue to avoid blocking request handlers"""
import threading
import queue
from PIL import Image


_image_queue = queue.Queue()
_worker_thread = None


def _process_images():
    """Worker thread that processes image resize tasks from the queue"""
    while True:
        task = _image_queue.get()
        if task is None:
            break
        path, target_size = task
        try:
            with Image.open(path) as img:
                resized = img.resize(target_size)
                resized.save(path)
        except Exception:
            pass
        _image_queue.task_done()


def start_worker():
    """Start the background image processing worker thread"""
    global _worker_thread
    if _worker_thread is None:
        _worker_thread = threading.Thread(target=_process_images, daemon=True)
        _worker_thread.start()


def queue_resize(path: str, size: tuple = (256, 256)):
    """Queue an image for background resizing"""
    _image_queue.put((path, size))
