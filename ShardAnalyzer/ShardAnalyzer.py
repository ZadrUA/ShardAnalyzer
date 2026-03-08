import sys
import re
import os
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, 
                             QComboBox, QGridLayout, QLabel, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QTimer

class ShardAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shard analyzer")
        
        self.log_path = ""
        self.analyses = []
        self.cell_widgets = {}
        self.last_mod_time = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)

        self.init_ui()
        self.apply_topmost(True)

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #121211; color: #ccc6a7; font-family: 'Segoe UI', sans-serif; }
            #MainContainer { background-color: #1a1a1a; border: 1px solid #b39c5a; border-radius: 10px; margin: 10px; }
            QPushButton { background-color: #1c1c1b; border: 1px solid #565341; padding: 10px; color: #fff; font-weight: bold; border-radius: 4px; min-width: 40px; }
            QPushButton:hover { background-color: #333; border-color: #b39c5a; }
            QComboBox { background-color: #1c1c1b; border: 1px solid #444; color: #eee; padding: 5px; }
            QLabel#Cell { background-color: #1c1c1b; border: 1px solid #333; font-size: 11px; }
            QLabel#Source { background-color: #1c1c1b; color: #fff; font-weight: bold; border: 1px solid #b39c5a; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainContainer")
        outer_layout.addWidget(self.main_frame)
        
        layout = QVBoxLayout(self.main_frame)
        header = QHBoxLayout()
        
        self.btn_open = QPushButton("SELECT LOG FILE")
        self.btn_open.clicked.connect(self.open_file)
        self.btn_prev = QPushButton(" < ")
        self.btn_prev.clicked.connect(self.go_prev)
        self.btn_next = QPushButton(" > ")
        self.btn_next.clicked.connect(self.go_next)
        
        self.history_combo = QComboBox()
        self.history_combo.setFixedWidth(150)
        self.history_combo.currentIndexChanged.connect(self.display_selected_analysis)
        
        self.chk_top = QCheckBox("Always on top")
        self.chk_top.setChecked(True)
        self.chk_top.stateChanged.connect(self.toggle_always_on_top)
        
        header.addWidget(self.btn_open)
        header.addSpacing(10)
        header.addWidget(self.btn_prev)
        header.addWidget(self.btn_next)
        header.addWidget(self.history_combo)
        header.addWidget(self.chk_top)
        header.addStretch(1)
        
        layout.addLayout(header)

        self.status_lbl = QLabel("Select a file to start")
        self.status_lbl.setStyleSheet("color: #666; font-size: 10px; margin-left: 5px;")
        layout.addWidget(self.status_lbl)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(1)
        self.build_accurate_grid()
        layout.addWidget(self.grid_widget)

    def toggle_always_on_top(self, state):
            # state == 2 означает Qt.CheckState.Checked
            self.apply_topmost(state == 2)

    def apply_topmost(self, is_top):
        flags = self.windowFlags()
            
        self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            
        if is_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            
        self.show()

    def build_accurate_grid(self):
        elements = [
            (0, 0, 1, 1, "i-nw"), (0, 1, 1, 5, "i-won"), (0, 6, 1, 1, "i-n"), (0, 7, 1, 5, "i-eon"), (0, 12, 1, 1, "i-ne"),
            (1, 0, 5, 1, "i-now"), (1, 12, 5, 1, "i-noe"), (1, 1, 1, 1, "v-nw"), (1, 2, 1, 4, "v-won"), (1, 6, 1, 1, "v-n"), (1, 7, 1, 4, "v-eon"), (1, 11, 1, 1, "v-ne"),
            (2, 1, 4, 1, "v-now"), (2, 2, 1, 1, "m-nw"), (2, 3, 1, 3, "m-won"), (2, 6, 1, 1, "m-n"), (2, 7, 1, 3, "m-eon"), (2, 10, 1, 1, "m-ne"), (2, 11, 4, 1, "v-noe"),
            (3, 2, 3, 1, "m-now"), (3, 3, 1, 1, "f-nw"), (3, 4, 1, 2, "f-won"), (3, 6, 1, 1, "f-n"), (3, 7, 1, 2, "f-eon"), (3, 9, 1, 1, "f-ne"), (3, 10, 3, 1, "m-noe"),
            (4, 3, 2, 1, "f-now"), (4, 4, 1, 1, "s-nw"), (4, 5, 1, 1, "s-won"), (4, 6, 1, 1, "s-n"), (4, 7, 1, 1, "s-eon"), (4, 8, 1, 1, "s-ne"), (4, 9, 2, 1, "f-noe"),
            (5, 4, 1, 1, "s-now"), (5, 5, 1, 1, "t-nw"), (5, 6, 1, 1, "t-n"), (5, 7, 1, 1, "t-ne"), (5, 8, 1, 1, "s-noe"),
            (6, 0, 1, 1, "i-w"), (6, 1, 1, 1, "v-w"), (6, 2, 1, 1, "m-w"), (6, 3, 1, 1, "f-w"), (6, 4, 1, 1, "s-w"), (6, 5, 1, 1, "t-w"),
            (6, 6, 1, 1, "c"), (6, 7, 1, 1, "t-e"), (6, 8, 1, 1, "s-e"), (6, 9, 1, 1, "f-e"), (6, 10, 1, 1, "m-e"), (6, 11, 1, 1, "v-e"), (6, 12, 1, 1, "i-e"),
            (7, 0, 5, 1, "i-sow"), (7, 1, 4, 1, "v-sow"), (7, 2, 3, 1, "m-sow"), (7, 3, 2, 1, "f-sow"), (7, 4, 1, 1, "s-sow"), (7, 5, 1, 1, "t-sw"), (7, 6, 1, 1, "t-s"), (7, 7, 1, 1, "t-se"), (7, 8, 1, 1, "s-soe"), (7, 9, 2, 1, "f-soe"), (7, 10, 3, 1, "m-soe"), (7, 11, 4, 1, "v-soe"), (7, 12, 5, 1, "i-soe"),
            (8, 4, 1, 1, "s-sw"), (8, 5, 1, 1, "s-wos"), (8, 6, 1, 1, "s-s"), (8, 7, 1, 1, "s-eos"), (8, 8, 1, 1, "s-se"),
            (9, 3, 1, 1, "f-sw"), (9, 4, 1, 2, "f-wos"), (9, 6, 1, 1, "f-s"), (9, 7, 1, 2, "f-eos"), (9, 9, 1, 1, "f-se"),
            (10, 2, 1, 1, "m-sw"), (10, 3, 1, 3, "m-wos"), (10, 6, 1, 1, "m-s"), (10, 7, 1, 3, "m-eos"), (10, 10, 1, 1, "m-se"),
            (11, 1, 1, 1, "v-sw"), (11, 2, 1, 4, "v-wos"), (11, 6, 1, 1, "v-s"), (11, 7, 1, 4, "v-eos"), (11, 11, 1, 1, "v-se"),
            (12, 0, 1, 1, "i-sw"), (12, 1, 1, 5, "i-wos"), (12, 6, 1, 1, "i-s"), (12, 7, 1, 5, "i-eos"), (12, 12, 1, 1, "i-se"),
        ]
        for r, c, rs, cs, cell_id in elements:
            lbl = QLabel("SOURCE" if cell_id == "c" else "")
            lbl.setObjectName("Source" if cell_id == "c" else "Cell")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setMinimumSize(50, 42)
            self.grid_layout.addWidget(lbl, r, c, rs, cs)
            self.cell_widgets[cell_id] = lbl

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Log", "", "Text Files (*.txt)")
        if path:
            self.log_path = path
            self.status_lbl.setText(f"Monitoring: {os.path.basename(path)}")
            self.refresh_data()

    def go_prev(self):
        idx = self.history_combo.currentIndex()
        if idx > 0: self.history_combo.setCurrentIndex(idx - 1)

    def go_next(self):
        idx = self.history_combo.currentIndex()
        if idx < self.history_combo.count() - 1: self.history_combo.setCurrentIndex(idx + 1)

    def refresh_data(self):
        if not self.log_path or not os.path.exists(self.log_path): return
        try:
            current_mod_time = os.path.getmtime(self.log_path)
            if current_mod_time > self.last_mod_time:
                self.last_mod_time = current_mod_time
                content = ""
                for enc in ['utf-8', 'cp1252']:
                    try:
                        with open(self.log_path, 'r', encoding=enc, errors='ignore') as f:
                            content = f.read()
                        break
                    except: continue
                
                pattern = re.compile(r"\[\d{2}:\d{2}:\d{2}\] You start to analyse.*?You finish analysing.*?\.", re.DOTALL)
                new_analyses = pattern.findall(content)
                if len(new_analyses) != len(self.analyses):
                    self.analyses = new_analyses
                    self.update_history_combo()
        except Exception: pass

    def update_history_combo(self):
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        for i, data in enumerate(self.analyses):
            time = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", data).group(1)
            self.history_combo.addItem(f"Analysis at {time}", i)
        if self.analyses: self.history_combo.setCurrentIndex(len(self.analyses) - 1)
        self.history_combo.blockSignals(False)
        self.display_selected_analysis(len(self.analyses) - 1)
        self.adjustSize()

    def display_selected_analysis(self, index):
        if index < 0 or index >= len(self.analyses): return
        for key, lbl in self.cell_widgets.items():
            if key != "c":
                lbl.setText(""); lbl.setStyleSheet("background-color: #1c1c1b;")
        text = self.analyses[index]
        regex_normal = re.compile(r"You (?:notice|spot|see) (?:a|an) (.*?) of (.*?) \((.*?)\)\.")
        regex_unknown = re.compile(r"You (?:notice|spot|see) (?:a|an) (.*?) of something, but cannot quite make it out \((.*?)\)\.")
        for line in text.split('\n'):
            line = line.strip()
            m_unk = regex_unknown.search(line)
            if m_unk:
                trace_type, direction = m_unk.groups()
                cell_id = self.get_cell_id(trace_type, direction)
                if cell_id in self.cell_widgets:
                    self.cell_widgets[cell_id].setText("<b>?</b>")
                    self.cell_widgets[cell_id].setStyleSheet("background-color: #111; color: #777; border: 1px solid #444;")
                continue
            m_norm = regex_normal.search(line)
            if m_norm:
                trace_type, material, direction = m_norm.groups()
                q_data = self.get_quality_data(material)
                cell_id = self.get_cell_id(trace_type, direction)
                if cell_id in self.cell_widgets:
                    self.cell_widgets[cell_id].setText(f"<b>{q_data['name']}</b><br><span style='font-size: 9px;'>{q_data['range']}</span>")
                    self.cell_widgets[cell_id].setStyleSheet(f"background-color: #111; color: {q_data['color']}; border: 1px solid #565341;")
        self.adjustSize()

    def get_quality_data(self, text):
        qs = {'utmost quality ': ('95-99', '#FF8000'), 'very good quality ': ('80-94', '#A335EE'), 
              'good quality ': ('60-79', '#0070FF'), 'normal quality ': ('40-59', '#1EFF00'), 
              'acceptable quality ': ('30-39', '#ffffff'), 'poor quality ': ('20-29', '#9D9D9D')}
        for k, v in qs.items():
            if text.lower().startswith(k): return {'name': text[len(k):].capitalize(), 'range': v[0], 'color': v[1]}
        return {'name': text.capitalize(), 'range': '', 'color': '#ccc'}

    def get_cell_id(self, trace, direction):
        t_map = {'trace':'t', 'slight trace':'s', 'faint trace':'f', 'minuscule trace':'m', 'vague trace':'v', 'indistinct trace':'i'}
        d_map = {'north':'n', 'east':'e', 'south':'s', 'west':'w', 'northwest':'nw', 'northeast':'ne', 'southwest':'sw', 'southeast':'se',
                 'north of west':'now', 'north of east':'noe', 'east of north':'eon', 'west of north':'won',
                 'south of west':'sow', 'south of east':'soe', 'east of south':'eos', 'west of south':'wos'}
        return f"{t_map.get(trace.lower(), 't')}-{d_map.get(direction.lower(), direction)}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShardAnalyzer()
    window.show()
    sys.exit(app.exec())