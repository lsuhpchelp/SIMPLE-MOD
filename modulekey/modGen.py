import sys, json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QTextEdit, QComboBox, QPushButton, QLabel, QDialog, QFormLayout)

with open("modDB.json") as f:
    db = json.load(f)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create widgets
        
        #--------------------------------------------------------
        
        # Module name
        self.nameDrop = QComboBox(self)
        self.nameDrop.addItems(sorted(list(db.keys())))
        self.nameDrop.currentIndexChanged.connect(self.updateModVersion)
        
        # Module version
        self.versionDrop = QComboBox(self)
        self.updateModVersion(0)
        
        # Add / edit buttons
        self.addBtn = QPushButton("Add a new module", self)
        self.addBtn.clicked.connect(self.add)
        self.editBtn = QPushButton("Edit selected module", self)
        self.editBtn.clicked.connect(self.edit)
        self.addEditBtnsLayout = QHBoxLayout()
        self.addEditBtnsLayout.addWidget(self.editBtn)
        self.addEditBtnsLayout.addWidget(self.addBtn)
        
        # Combine header
        self.headerLayout = QFormLayout()
        self.headerLayout.addRow("Module name", self.nameDrop)
        self.headerLayout.addRow("Module version", self.versionDrop)
        self.headerLayout.addRow(self.addEditBtnsLayout)
        
        #--------------------------------------------------------
        
        # Conflicts
        self.conflictText = QLineEdit(self)
        
        # What-is
        self.whatisText = QLineEdit(self)
        
        # Singularity image path
        self.singularityImageText = QLineEdit(self)
        
        # Singularity binding path
        self.singularityBindText = QLineEdit(self)
        
        # Singularity flags
        self.singularityFlagsText = QLineEdit(self)
        
        # Commands to replace
        self.cmdsText = QTextEdit(self)
        
        # Environment variables to set up
        self.envsLayout = QVBoxLayout()
        
        # Combine module edit layout
        self.moduleEditLayout = QFormLayout()
        self.moduleEditLayout.addRow("Conflicts (seperate by space)", self.conflictText)
        self.moduleEditLayout.addRow("Software description", self.whatisText)
        self.moduleEditLayout.addRow("Singularity image path", self.singularityImageText)
        self.moduleEditLayout.addRow("Singularity binding paths", self.singularityBindText)
        self.moduleEditLayout.addRow("Singularity flags", self.singularityFlagsText)
        self.moduleEditLayout.addRow("Commands to replace \n (seperate by space or new line)", self.cmdsText)
        self.moduleEditLayout.addRow("Set up environmental variable", self.envsLayout)
            
        #--------------------------------------------------------

        # Create main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.headerLayout)
        self.mainLayout.addWidget(QLabel("", self))
        self.mainLayout.addLayout(self.moduleEditLayout)

        # Create container
        container = QWidget()
        container.setLayout(self.mainLayout)
        self.setCentralWidget(container)

        # Set main window properties
        self.setWindowTitle("QT5 Window")
        self.setGeometry(100, 100, 600, 600)

    def updateModVersion(self, index):
        self.versionDrop.clear()
        self.versionDrop.addItems(db[self.nameDrop.currentText()])

    def add(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add a new module")

        layout = QFormLayout()

        dialog.nameText = QLineEdit(dialog)
        dialog.nameText.setPlaceholderText("Module name")
        layout.addRow("Module name", dialog.nameText)

        dialog.versionText = QLineEdit(dialog)
        dialog.versionText.setPlaceholderText("Module versuib")
        layout.addRow("Module version", dialog.versionText)

        dialog.setLayout(layout)

        dialog.exec_()

    def edit(self):
        pass
        
    def addENV(self, envLayout):
        pass
        
    def updateENV(self, envLayout):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
