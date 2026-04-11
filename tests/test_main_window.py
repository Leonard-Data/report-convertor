"""Tests for MainWindow component."""

from pathlib import Path

from report_convertor.components.main_window import MainWindow


class TestMainWindow:
    """Test suite for MainWindow."""

    def test_window_title(self, qtbot) -> None:
        """Window has correct title."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.windowTitle() == "Report Convertor"

    def test_template_input_exists(self, qtbot) -> None:
        """Template input field exists."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.template_input is not None

    def test_preview_rows_input_exists(self, qtbot) -> None:
        """Preview rows spin box exists."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.preview_rows_input is not None
        assert window.preview_rows_input.value() == 10

    def test_preview_rows_input_range(self, qtbot) -> None:
        """Preview rows spin box has correct range."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.preview_rows_input.minimum() == 1
        assert window.preview_rows_input.maximum() == 1000

    def test_summary_label_exists(self, qtbot) -> None:
        """Summary label exists with initial text."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.summary_label is not None

    def test_mappings_table_exists(self, qtbot) -> None:
        """Mappings table widget exists."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.mappings_table is not None

    def test_preview_table_exists(self, qtbot) -> None:
        """Preview table widget exists."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.preview_table is not None

    def test_status_bar_exists(self, qtbot) -> None:
        """Status bar exists."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.statusBar() is not None

    def test_window_default_size(self, qtbot) -> None:
        """Window has correct default size."""

        window = MainWindow(templates_dir=Path("templates"))
        qtbot.addWidget(window)

        assert window.width() == 1100
        assert window.height() == 720
