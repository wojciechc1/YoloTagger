from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFileDialog, QLabel

class YamlSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select YOLO Dataset YAML")
        self.setGeometry(100, 100, 400, 100)

        self.selected_path = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("No file selected")
        layout.addWidget(self.label)

        btn_select = QPushButton("Choose YAML")
        btn_select.clicked.connect(self.choose_yaml)
        layout.addWidget(btn_select)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

    def choose_yaml(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select YOLO Dataset YAML",
            "",
            "YAML Files (*.yaml *.yml)"
        )
        if path:
            self.selected_path = path
            self.label.setText(path)

    def get_path(self):
        return self.selected_path