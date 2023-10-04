import sys, json
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, 
                             QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QDialog)

with open("modDB.json") as f:
    db = json.load(f)

currentModule = {
    "conflict":                 "",
    "module_whatis":            "",
    "singularity_image":        "",
    "singularity_bindpaths":    "",
    "singularity_flags":        "",
    "cmds":                     "",
    "envs":                     {  }
}

# Main window
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Create widgets
        
        #--------------------------------------------------------
        # Block1: Choose / create module
        
        # Header
        self.blk1Label = QLabel('Module List')
        self.blk1Label.setStyleSheet('QLabel { font-size: 16px; font-weight: bold; }')
        
        # Module name
        self.nameDrop = QComboBox(self)
        self.updateModName()
        self.nameDrop.textActivated.connect(self.updateModVersion)
        
        # Module version
        self.versionDrop = QComboBox(self)
        self.versionDrop.textActivated.connect(self.updateModDetail)
        
        # Add / edit buttons
        self.addBtn = QPushButton("Add a new module", self)
        self.addBtn.clicked.connect(self.addMod)
        
        # Combine module choose layout
        self.moduleChooseLayout = QFormLayout()
        self.moduleChooseLayout.addRow("Module name", self.nameDrop)
        self.moduleChooseLayout.addRow("Module version", self.versionDrop)
        self.moduleChooseLayout.addRow(self.addBtn)
        
        #--------------------------------------------------------
        # Block2: Module details
        
        # Header
        self.blk2Label = QLabel('Module Details')
        self.blk2Label.setStyleSheet('QLabel { font-size: 16px; font-weight: bold; }')
        
        # Conflicts
        self.conflictText = QLineEdit(self)
        self.conflictText.setPlaceholderText("(Seperate by space. Do not add itself.)")
        pal = self.conflictText.palette()
        pal.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#BBBBBB"))
        self.conflictText.setPalette(pal)
        
        # What-is
        self.whatisText = QLineEdit(self)
        
        # Singularity image path
        self.singularityImageText = QLineEdit(self)
        
        # Singularity binding path
        self.singularityBindText = QLineEdit(self)
        self.singularityBindText.setPlaceholderText("(Bound by default: /home,/work,/project,/usr/local/packages,/ddnA,/var/scratch,/tmp)")
        pal = self.singularityBindText.palette()
        pal.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#BBBBBB"))
        self.singularityBindText.setPalette(pal)
        
        # Singularity flags
        self.singularityFlagsText = QLineEdit(self)
        
        # Commands to replace
        self.cmdsText = QTextEdit(self)
        self.cmdsText.setPlaceholderText("Seperate by space or new line")
        pal = self.cmdsText.palette()
        pal.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#BBBBBB"))
        self.cmdsText.setPalette(pal)
        
        # Environment variables to set up
        self.envsTable = QTableWidget(1, 2, self)
        self.envsUpdate()
        
        # Environment variables add / delete entry
        self.envsAddBtn =  QPushButton("Add", self)
        self.envsAddBtn.clicked.connect(self.envsAdd)
        self.envsDelBtn =  QPushButton("Delete", self)
        self.envsDelBtn.clicked.connect(self.envsDel)
        self.envsBtnLayout = QHBoxLayout()
        self.envsBtnLayout.addWidget(self.envsAddBtn)
        self.envsBtnLayout.addWidget(self.envsDelBtn)
        
        # Combine module edit layout
        self.moduleEditLayout = QFormLayout()
        self.moduleEditLayout.addRow("Conflicts", self.conflictText)
        #self.moduleEditLayout.addRow("", QLabel("(Seperate by space. Itself will be added by default.)"))
        self.moduleEditLayout.addRow("Software description", self.whatisText)
        self.moduleEditLayout.addRow("Singularity image path", self.singularityImageText)
        self.moduleEditLayout.addRow("Singularity binding paths", self.singularityBindText)
        #self.moduleEditLayout.addRow("", QLabel("(Bound by default: /home,/work,/project,/usr/local/packages,/ddnA,/var/scratch,/tmp)"))
        self.moduleEditLayout.addRow("Singularity flags", self.singularityFlagsText)
        self.moduleEditLayout.addRow("Commands to replace", self.cmdsText)
        self.moduleEditLayout.addRow("Set up environmental variable", self.envsTable)
        self.moduleEditLayout.addRow("", self.envsBtnLayout)
        
        #--------------------------------------------------------
        # Block3: Confirmation buttons
        
        # Add / edit buttons
        self.saveBtn = QPushButton("Save to database", self)
        self.saveBtn.clicked.connect(self.save)
        self.genBtn = QPushButton("Generate this module key", self)
        self.genBtn.clicked.connect(self.gen)
        self.exportBtn = QPushButton("Generate all module keys from database", self)
        self.exportBtn.clicked.connect(self.export)
        self.confirmationBtnsLayout = QHBoxLayout()
        self.confirmationBtnsLayout.addWidget(self.saveBtn)
        self.confirmationBtnsLayout.addWidget(self.genBtn)
        self.confirmationBtnsLayout.addWidget(self.exportBtn)
            
        #--------------------------------------------------------

        # Create main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.blk1Label)
        self.mainLayout.addLayout(self.moduleChooseLayout)
        self.mainLayout.addWidget(QLabel("", self))
        self.mainLayout.addWidget(self.blk2Label)
        self.mainLayout.addLayout(self.moduleEditLayout)
        self.mainLayout.addWidget(QLabel("", self))
        self.mainLayout.addLayout(self.confirmationBtnsLayout)

        # Create container
        container = QWidget()
        container.setLayout(self.mainLayout)
        self.setCentralWidget(container)

        # Set main window properties
        self.setWindowTitle("Containerized App Modulekey Producer (CAMP) v1.0")
        self.setGeometry(100, 100, 750, 700)

    def updateModName(self):
        self.nameDrop.clear()
        self.nameDrop.addItems(sorted(db.keys()))

    def updateModVersion(self):
        self.versionDrop.clear()
        self.versionDrop.addItems(sorted(db[self.nameDrop.currentText()].keys()))
        self.updateModDetail()

    def addMod(self):
    
        # Open a dialog
        newModDial = NewModuleDialog(self)
        
        # If confirmed, create module
        if newModDial.exec_():
            
            # Create new module in db dictionary
            
            # Check a module with the same name already exist:
            if (newModDial.modNameText.text() in db.keys()):
                if (newModDial.modVersionText.text() in db[newModDial.modNameText.text()].keys()):
                    QMessageBox.warning(self, 'Warning', 'Module of the same name and version already exists!')
                else:
                    db[newModDial.modNameText.text()][newModDial.modVersionText.text()] = { 
                        "conflict":                 "",
                        "module_whatis":            "",
                        "singularity_image":        "",
                        "singularity_bindpaths":    "",
                        "singularity_flags":        "",
                        "cmds":                     "",
                        "envs":                     {  }
                    }
                    
            else:
                db[newModDial.modNameText.text()] = { 
                    newModDial.modVersionText.text() : {
                        "conflict":                 "",
                        "module_whatis":            "",
                        "singularity_image":        "",
                        "singularity_bindpaths":    "",
                        "singularity_flags":        "",
                        "cmds":                     "",
                        "envs":                     {  }
                    }
                }
                
            # Update dropdown menu
            self.updateModName()
            self.nameDrop.setCurrentText(newModDial.modNameText.text())
            self.updateModVersion()
            self.versionDrop.setCurrentText(newModDial.modVersionText.text())
            self.updateModDetail()

    def envsAdd(self):
        self.envsTable.setRowCount(self.envsTable.rowCount()+1)
        item = QTableWidgetItem(f"ENV_{self.envsTable.rowCount()}")
        self.envsTable.setItem(self.envsTable.rowCount()-1, 0, item)
        item = QTableWidgetItem("")
        self.envsTable.setItem(self.envsTable.rowCount()-1, 1, item)
     
    def envsUpdate(self):
        
        # Clear current values
        self.envsTable.clear()
        
        # Reset table
        keys = list(currentModule["envs"].keys())
        self.envsTable.setHorizontalHeaderLabels(["Name", "Value"])
        self.envsTable.setRowCount(len(keys))
        
        # Add new entries
        for row in range(len(keys)):
            item = QTableWidgetItem(keys[row])
            self.envsTable.setItem(row, 0, item)
            item = QTableWidgetItem(currentModule["envs"][keys[row]])
            self.envsTable.setItem(row, 1, item)
     
    def envsSave(self, clearFirst=True):
    
        # Clear the current data in currentModule
        if clearFirst:
            currentModule["envs"] = {}
        
        # Save current values in the table to dictionary
        for row in range(self.envsTable.rowCount()):
            if self.envsTable.item(row,0) and self.envsTable.item(row,1):
                currentModule["envs"][self.envsTable.item(row,0).text()] = self.envsTable.item(row,1).text()

    def envsDel(self):
        items = self.envsTable.selectedItems()
        for item in items:
            self.envsTable.removeRow(item.row())

    def save(self):
    
        # Confirm first
        confirmationDial = ConfirmationDialog(self)
        
        # If confirmed, save module
        if confirmationDial.exec_():
        
            # Set currentModule to the values in the fields
            currentModule["conflict"] = self.conflictText.text()
            currentModule["module_whatis"] = self.whatisText.text()
            currentModule["singularity_image"] = self.singularityImageText.text()
            currentModule["singularity_bindpaths"] = self.singularityBindText.text()
            currentModule["singularity_flags"] = self.singularityFlagsText.text()
            currentModule["cmds"] = self.cmdsText.toPlainText()
            self.envsSave()
            
            # Save changes
            db[self.nameDrop.currentText()][self.versionDrop.currentText()] = currentModule
            with open(confirmationDial.dbname.text(), "w") as fw:
                json.dump(db, fw, indent=4)

    def gen(self):
        with open("test.txt", "w") as fw:
            fw.write(self.cmdsText.toPlainText())

    def export(self):
        pass
        
    def resizeEnvsColumns(self):
        self.envsTable.setColumnWidth(0, int(0.28*self.envsTable.width()))
        self.envsTable.setColumnWidth(1, int(0.68*self.envsTable.width()))

    def resizeEvent(self, event):
        self.resizeEnvsColumns()
        super().resizeEvent(event)
     
    def updateModDetail(self):
    
        global currentModule
        currentModule = db[self.nameDrop.currentText()][self.versionDrop.currentText()]
    
        # Set all values from currentModule dict
        self.conflictText.setText(currentModule["conflict"])
        self.whatisText.setText(currentModule["module_whatis"])
        self.singularityImageText.setText(currentModule["singularity_image"])
        self.singularityBindText.setText(currentModule["singularity_bindpaths"])
        self.singularityFlagsText.setText(currentModule["singularity_flags"])
        self.cmdsText.setText(currentModule["cmds"])
        
        # Update environmental variables table separately
        self.envsUpdate()
    
    def checkUnsavedChanges(self):
        """
        Check current form against currentModule dictionary to see if there is any unsaved changes
        """
        pass
        
# New module dialog
class NewModuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create text field to enter database name
        self.modNameText = QLineEdit(self)
        self.modVersionText = QLineEdit(self)
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Module name:", self.modNameText)
        self.formLayout.addRow("Module version:", self.modVersionText)

        # Create buttons
        self.confirmBtn = QPushButton('Confirm', self)
        self.confirmBtn.clicked.connect(self.checkEmpty)
        self.cancelBtn = QPushButton('Cancel', self)
        self.cancelBtn.clicked.connect(self.reject)

        # Create button layout and add buttons
        self.btnLayout = QHBoxLayout()
        self.btnLayout.addWidget(self.confirmBtn)
        self.btnLayout.addWidget(self.cancelBtn)
        
        # Create entire layout
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.formLayout)
        self.layout.addLayout(self.btnLayout)
        self.setLayout(self.layout)
        self.setWindowTitle("Add a new module")
    
    def checkEmpty(self):
        if not self.modNameText.text().strip() or not self.modVersionText.text().strip():
            QMessageBox.warning(self, 'Warning', 'Module name and version cannot be empty!')
        else:
            self.accept() 
        
# Confirmation dialog
class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create text field to enter database name
        self.dbname = QLineEdit(self)
        self.dbname.setText("modDB.json")
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Database name:", self.dbname)

        # Create buttons
        self.confirmBtn = QPushButton('Confirm', self)
        self.confirmBtn.clicked.connect(self.accept)
        self.cancelBtn = QPushButton('Cancel', self)
        self.cancelBtn.clicked.connect(self.reject)

        # Create button layout and add buttons
        self.btnLayout = QHBoxLayout()
        self.btnLayout.addWidget(self.confirmBtn)
        self.btnLayout.addWidget(self.cancelBtn)
        
        # Create entire layout
        self.layout = QVBoxLayout()
        self.msg = QLabel("Save to file. Changes are irreversible!")
        self.layout.addWidget(self.msg)
        self.layout.addLayout(self.formLayout)
        self.layout.addLayout(self.btnLayout)
        self.setLayout(self.layout)
        self.setWindowTitle("Confirm")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.resizeEnvsColumns()
    mainWindow.updateModVersion()
    sys.exit(app.exec_())
