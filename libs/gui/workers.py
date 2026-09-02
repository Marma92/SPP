"""Everything slow runs off the interface thread.

Resizing a 6000px scan takes a moment and an upload takes many; doing either
on the UI thread freezes the window.
"""

from PySide6.QtCore import QThread, Signal

from libs import runner


class PrepareWorker(QThread):
    """Prepares the picture for every platform, one after the other."""

    ready = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, publishers, post, parent=None):
        super().__init__(parent)
        self._publishers = list(publishers)
        self._post = post

    def run(self):
        for publisher in self._publishers:
            try:
                image = publisher.prepare_image(self._post)
            except Exception as error:
                self.failed.emit(publisher.name, str(error))
                continue
            self.ready.emit(publisher.name, str(image))


class PublishWorker(QThread):
    """Drives one publishing run and relays its events."""

    progress = Signal(object)

    def __init__(self, publishers, post, images, dry_run=False, parent=None):
        super().__init__(parent)
        self._publishers = list(publishers)
        self._post = post
        self._images = dict(images)
        self._dry_run = dry_run

    def run(self):
        for event in runner.run(
            self._publishers, self._post, self._dry_run, self._images
        ):
            self.progress.emit(event)
