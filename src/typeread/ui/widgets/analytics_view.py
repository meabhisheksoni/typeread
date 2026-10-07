"""
TypeRead Analytics & Performance Dashboard Widget
Renders metrics overview, daily trends, weak-key breakdown, and drill generator.
Handles empty, loading, and populated states cleanly.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal

from src.typeread.ui.widgets.theme_manager import ThemeManager


class AnalyticsView(QWidget):
    """
    Statistics Dashboard displaying user progress, trends, and weak keys.
    """

    generate_drill_requested = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = "dark"
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Title
        title_box = QHBoxLayout()
        self.title_lbl = QLabel("ANALYTICS & RETENTION DASHBOARD", self)
        f = self.title_lbl.font()
        f.setPointSize(18)
        f.setBold(True)
        self.title_lbl.setFont(f)
        title_box.addWidget(self.title_lbl)
        title_box.addStretch()

        self.refresh_btn = QPushButton("Refresh", self)
        title_box.addWidget(self.refresh_btn)
        main_layout.addLayout(title_box)

        # Scroll Area for Content
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)

        # 1. Summary Cards Frame
        self.summary_frame = QFrame(content)
        self.summary_frame.setObjectName("cardFrame")
        s_layout = QHBoxLayout(self.summary_frame)
        s_layout.setSpacing(20)

        self.card_wpm = self._create_stat_card("AVG NET WPM", "0")
        self.card_acc = self._create_stat_card("ACCURACY", "0.0%")
        self.card_time = self._create_stat_card("PRACTICE TIME", "0m")
        self.card_chars = self._create_stat_card("CHARS TYPED", "0")
        self.card_sessions = self._create_stat_card("SESSIONS", "0")

        s_layout.addWidget(self.card_wpm["frame"])
        s_layout.addWidget(self.card_acc["frame"])
        s_layout.addWidget(self.card_time["frame"])
        s_layout.addWidget(self.card_chars["frame"])
        s_layout.addWidget(self.card_sessions["frame"])
        self.content_layout.addWidget(self.summary_frame)

        # 2. Weak-Keys & Targeted Drills Section
        weak_frame = QFrame(content)
        weak_frame.setObjectName("cardFrame")
        w_layout = QVBoxLayout(weak_frame)
        w_layout.setSpacing(12)

        w_header = QHBoxLayout()
        w_title = QLabel("WEAK-KEY ANALYSIS & TARGETED DRILLS", weak_frame)
        w_title.setObjectName("sectionHeading")
        w_header.addWidget(w_title)
        w_header.addStretch()

        self.drill_btn = QPushButton("Generate Targeted Drill", weak_frame)
        self.drill_btn.setObjectName("primaryBtn")
        w_header.addWidget(self.drill_btn)
        w_layout.addLayout(w_header)

        self.weak_table = QTableWidget(weak_frame)
        self.weak_table.setColumnCount(4)
        self.weak_table.setHorizontalHeaderLabels(["Key", "Errors", "Occurrences", "Error Rate"])
        self.weak_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.weak_table.setMinimumHeight(180)
        w_layout.addWidget(self.weak_table)

        self.content_layout.addWidget(weak_frame)

        # 3. Daily Practice Trend Frame
        self.trend_frame = QFrame(content)
        self.trend_frame.setObjectName("cardFrame")
        t_layout = QVBoxLayout(self.trend_frame)
        t_title = QLabel("DAILY PRACTICE ACTIVITY", self.trend_frame)
        t_title.setObjectName("sectionHeading")
        t_layout.addWidget(t_title)

        self.trend_container = QVBoxLayout()
        t_layout.addLayout(self.trend_container)
        self.content_layout.addWidget(self.trend_frame)

        self.content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _create_stat_card(self, label: str, value: str) -> Dict[str, Any]:
        frame = QFrame()
        frame.setObjectName("cardFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("metricValue")
        lbl = QLabel(label)
        lbl.setObjectName("metricLabel")

        layout.addWidget(val_lbl)
        layout.addWidget(lbl)
        return {"frame": frame, "val": val_lbl, "lbl": lbl}

    def set_theme(self, theme: str) -> None:
        self.theme = theme

    def display_data(
        self,
        overview: Dict[str, Any],
        weak_keys: List[Dict[str, Any]],
        trends: Dict[str, Any],
    ) -> None:
        # Overview
        wpm = overview.get("average_net_wpm", 0.0)
        acc = overview.get("average_accuracy_pct", 0.0)
        secs = overview.get("total_practice_seconds", 0)
        chars = overview.get("total_characters_typed", 0)
        sessions = overview.get("total_sessions", 0)

        mins = secs // 60
        hours = mins // 60
        time_str = f"{hours}h {mins % 60}m" if hours > 0 else f"{mins}m"

        self.card_wpm["val"].setText(f"{int(wpm)}")
        self.card_acc["val"].setText(f"{acc:.1f}%")
        self.card_time["val"].setText(time_str)
        self.card_chars["val"].setText(f"{chars:,}")
        self.card_sessions["val"].setText(f"{sessions}")

        # Weak keys
        self.weak_table.setRowCount(len(weak_keys))
        for row, wk in enumerate(weak_keys):
            key_item = QTableWidgetItem(f"'{wk.get('character', '')}'")
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            err_item = QTableWidgetItem(str(wk.get("error_count", 0)))
            err_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            occ_item = QTableWidgetItem(str(wk.get("total_occurrences", 0)))
            occ_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rate_item = QTableWidgetItem(f"{wk.get('error_rate_pct', 0.0):.1f}%")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.weak_table.setItem(row, 0, key_item)
            self.weak_table.setItem(row, 1, err_item)
            self.weak_table.setItem(row, 2, occ_item)
            self.weak_table.setItem(row, 3, rate_item)

        # Trends
        # Clear previous trend bars
        while self.trend_container.count():
            item = self.trend_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        activity = trends.get("daily_activity", [])
        if not activity:
            empty_lbl = QLabel("No daily practice records found.", self.trend_frame)
            empty_lbl.setObjectName("textMuted")
            self.trend_container.addWidget(empty_lbl)
        else:
            for day in activity[:14]:  # Show up to 14 days
                row_box = QHBoxLayout()
                date_lbl = QLabel(day.get("date", ""), self.trend_frame)
                date_lbl.setFixedWidth(100)
                row_box.addWidget(date_lbl)

                bar = QProgressBar(self.trend_frame)
                bar.setRange(0, 3600)  # Up to 1 hour
                bar.setValue(min(3600, day.get("practice_seconds", 0)))
                row_box.addWidget(bar, stretch=1)

                info_lbl = QLabel(f"{day.get('practice_seconds', 0)//60}m | {day.get('avg_net_wpm', 0):.0f} WPM", self.trend_frame)
                info_lbl.setFixedWidth(110)
                row_box.addWidget(info_lbl)

                self.trend_container.addLayout(row_box)
