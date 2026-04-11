"""Background worker that generates review rows for the editor."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from report_convertor.features.mapping.preview_service import PreviewService


class ReviewWorker(QObject):
    """Generate preview rows on a background Qt thread."""

    review_ready = pyqtSignal(int, list)
    review_failed = pyqtSignal(int, str)

    @pyqtSlot(int, object, int)
    def generate_review(self, request_id: int, draft, row_count: int) -> None:
        """Build preview rows for the current draft.

        Args:
            request_id: Monotonic identifier used to ignore stale results.
            draft: Current template draft from the editor.
            row_count: Requested preview row count.
        """

        try:
            rows = PreviewService().preview_rows(draft, row_count=row_count)
        except (FileNotFoundError, ValueError, OSError) as error:
            self.review_failed.emit(request_id, str(error))
            return
        self.review_ready.emit(request_id, rows)
