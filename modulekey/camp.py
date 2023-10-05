import sys, json, os
from string import Template
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, 
                             QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QDialog)

with open("campDB.json") as f:
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

    #============================================================
    # Constructor
    #============================================================
    def __init__(self):
        """
        Constructor
        """
        
        super().__init__()

        # Create widgets
        
        #--------------------------------------------------------
        # Block1: Choose / create module
        
        # Header
        self.blk1Label = QLabel('Module List')
        self.blk1Label.setStyleSheet('QLabel { font-size: 16px; font-weight: bold; }')
        
        # Module name
        self.nameDrop = QComboBox(self)
        self.dropNameUpdateFromDB()
        self.nameDrop.textActivated.connect(self.dropVersionUpdateFromDB)
        
        # Module version
        self.versionDrop = QComboBox(self)
        self.versionDrop.textActivated.connect(self.modUpdateFromDB)
        
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
        self.envsUpdateFromDB()
        
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
        self.saveBtn.clicked.connect(self.saveToFile)
        self.genBtn = QPushButton("Generate this module key", self)
        self.genBtn.clicked.connect(self.genModKey)
        self.exportBtn = QPushButton("Generate all module keys from database", self)
        self.exportBtn.clicked.connect(self.genAllModKeys)
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

    #============================================================
    # Dropdown menu methods
    #============================================================

    def dropNameUpdateFromDB(self):
        """
        Update module name dropdown menu.
        """
        self.nameDrop.clear()
        self.nameDrop.addItems(sorted(db.keys()))

    def dropVersionUpdateFromDB(self):
        """
        Update module version dropdown menu.
        """
        self.versionDrop.clear()
        self.versionDrop.addItems(sorted(db[self.nameDrop.currentText()].keys()))
        self.modUpdateFromDB()

    #============================================================
    # Module form methods
    #============================================================
     
    def modUpdateFromDB(self):
        """
        Update module form from database ("currentModule" dictionary)
        """
    
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
        self.envsUpdateFromDB()
     
    def modSaveToDB(self):
        """
        Save module form to database ("currentModule" dictionary)
        """
        
        currentModule["conflict"] = self.conflictText.text()
        currentModule["module_whatis"] = self.whatisText.text()
        currentModule["singularity_image"] = self.singularityImageText.text()
        currentModule["singularity_bindpaths"] = self.singularityBindText.text()
        currentModule["singularity_flags"] = self.singularityFlagsText.text()
        currentModule["cmds"] = self.cmdsText.toPlainText()
        self.envsSaveToDB()

    #============================================================
    # Add / Delete module
    #============================================================

    def addMod(self):
        """
        Add a module
        """
    
        # Open a dialog
        newModDial = NewModuleDialog(self)
        
        # If confirmed, create module
        if newModDial.exec_():

            # Strip module name and version
            modName = newModDial.modNameText.text()
            modVersion = newModDial.modVersionText.text()
            
            # Check a module with the same name already exist:
            if (modName in db.keys()):
            
                # If the module of the same name and version exists, warn and do nother
                if (modVersion in db[modName].keys()):
                    QMessageBox.warning(self, 'Warning', 'Module of the same name and version already exists!')
                    
                else:
                
                    # If the module name is found but version is not, add a new version to existing module name
                    db[modName][modVersion] = { 
                        "conflict":                 "",
                        "module_whatis":            "",
                        "singularity_image":        "",
                        "singularity_bindpaths":    "",
                        "singularity_flags":        "",
                        "cmds":                     "",
                        "envs":                     {  }
                    }
                    
            else:
            
                # If the module name is not found, add a new module name
                db[modName] = { 
                    modVersion : {
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
            self.dropNameUpdateFromDB()
            self.nameDrop.setCurrentText(newModDial.modNameText.text())
            self.dropVersionUpdateFromDB()
            self.versionDrop.setCurrentText(newModDial.modVersionText.text())
            self.modUpdateFromDB()

    #============================================================
    # Environment variable table related methods
    #============================================================

    def envsAdd(self):
        """
        Add a new environmental variable.
        """
        self.envsTable.setRowCount(self.envsTable.rowCount()+1)
        item = QTableWidgetItem(f"ENV_{self.envsTable.rowCount()}")
        self.envsTable.setItem(self.envsTable.rowCount()-1, 0, item)
        item = QTableWidgetItem("")
        self.envsTable.setItem(self.envsTable.rowCount()-1, 1, item)

    def envsDel(self):
        """
        Delete the selected environmental variable(s).
        """
        items = self.envsTable.selectedItems()
        for item in items:
            self.envsTable.removeRow(item.row())
     
    def envsUpdateFromDB(self):
        """
        Update environmental variable table from database ("currentModule" dictionary)
        """
        
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
     
    def envsSaveToDB(self):
        """
        Save environmental variable table to database ("currentModule" dictionary)
        """
    
        # Clear the current data in currentModule
        currentModule["envs"] = {}
        
        # Save current values in the table to dictionary
        for row in range(self.envsTable.rowCount()):
            if self.envsTable.item(row,0) and self.envsTable.item(row,1):
                currentModule["envs"][self.envsTable.item(row,0).text()] = self.envsTable.item(row,1).text()

    #============================================================
    # Execution buttons methods
    #============================================================

    def saveToFile(self):
        """
        Save module form to file
        """
    
        # Confirm first
        confirmationDial = ConfirmationDialog(self)
        confirmationDial.msg.setText("Are you sure to save to this database? This change is irreversible!")
        
        # If confirmed, save module info to file
        if confirmationDial.exec_():
            
            # Set currentModule to the values in the fields
            self.modSaveToDB()
            
            # Save changes
            db[self.nameDrop.currentText()][self.versionDrop.currentText()] = currentModule
            with open(confirmationDial.dbname.text(), "w") as fw:
                json.dump(db, fw, indent=4)

    def genModKey(self):
        """
        Generate module key for current module
        """
    
        # Confirm first
        confirmationDial = ConfirmationDialog(self)
        confirmationDial.msg.setText("Changes will be saved to database before creating the module key. \nAre you sure to proceed? This change is irreversible!")
        
        # If confirmed, save module info to file and export module key
        if confirmationDial.exec_():
        
            # Set currentModule to the values in the fields
            self.modSaveToDB()
            
            # Save changes
            db[self.nameDrop.currentText()][self.versionDrop.currentText()] = currentModule
            with open(confirmationDial.dbname.text(), "w") as fw:
                json.dump(db, fw, indent=4)
            
            # Create folder if not exist
            pathModKey = f"{self.nameDrop.currentText()}/{self.versionDrop.currentText()}"
            dir = os.path.dirname(pathModKey)
            if not os.path.exists(dir):
                os.makedirs(dir)
            
            # Export module file
            with open(pathModKey, "w") as fw:
                fw.write(self.retModKey())

    def genAllModKeys(self):
        """
        Generate module keys for current database
        """
    
        # Confirm first
        confirmationDial = ConfirmationDialog(self)
        confirmationDial.msg.setText("Changes will be saved to database before creating the module keys. \nAre you sure to proceed? This change is irreversible!")
        
        # If confirmed, save module info to file and export module key
        if confirmationDial.exec_():
        
            # Set currentModule to the values in the fields
            self.modSaveToDB()
            
            # Save changes
            db[self.nameDrop.currentText()][self.versionDrop.currentText()] = currentModule
            with open(confirmationDial.dbname.text(), "w") as fw:
                json.dump(db, fw, indent=4)
                
            # Loop over all modules in db to create module keys
            for modName in db.keys():
                for modVersion in db[modName].keys():
                
                    # Create folder if not exist
                    pathModKey = f"{modName}/{modVersion}"
                    dir = os.path.dirname(pathModKey)
                    if not os.path.exists(dir):
                        os.makedirs(dir)
            
                    # Export module file
                    with open(pathModKey, "w") as fw:
                        fw.write(self.retModKey(modName, modVersion, db[modName][modVersion]))
        

    #============================================================
    # Module key template
    #============================================================

    def retModKey(self, modName=None , modVersion=None, dictModule=None):
        """
        Return module key from a template.
        """
        
        # Default module name, version, and module dictionary to current if not given
        modName = modName or self.nameDrop.currentText()
        modVersion = modVersion or self.versionDrop.currentText()
        dictModule = dictModule or currentModule
    
        # Parse environmental variable dictionary into a single string
        envsStr = ""
        for key, value in dictModule["envs"].items():
            envsStr += f"setenv {key} \"{value}\"\n"
        
        # Set up module key template
        tmpModKey = Template("""#%Module

# ---------------------------------------------------------------------
# Module setup (Edit this section for different modules)
# ---------------------------------------------------------------------

# Conflicts
conflict $modName $conflict

# Module information
module-whatis $whatis
module-version $modVersion

# Singularity options
set SINGULARITY_IMAGE "$singularity_image"
set SINGULARITY_BINDPATHS "$singularity_bindpaths"
set SINGULARITY_FLAGS "$singularity_flags"

# List of commands to overwrite
set cmds {
$cmds_dummy
}

# Set environment varialbles
$envs

# ---------------------------------------------------------------------
# Templates (Do not change this section)
# ---------------------------------------------------------------------

# Overwrite the list of commands upon loading
if { [ module-info mode load ] } {
    foreach cmd $cmds {
        if { [ module-info shelltype csh ] } {
            puts "alias $cmd singularity exec -B /work,/project,/usr/local/packages,/ddnA,/var/scratch,$SINGULARITY_BINDPATHS $SINGULARITY_FLAGS $SINGULARITY_IMAGE $cmd $*; "
        } elseif { [ module-info shelltype sh ] } {
            puts "$cmd () {"
            puts "    singularity exec -B /work,/project,/usr/local/packages,/ddnA,/var/scratch,$SINGULARITY_BINDPATHS $SINGULARITY_FLAGS $SINGULARITY_IMAGE $cmd $@"
            puts "}"
            puts "export -f $cmd"
        }
    }
}

# Unset commands upon unloading
if { [ module-info mode unload ] } {
    foreach cmd $cmds {
        if { [ module-info shelltype csh ] } {
            puts "unalias $cmd"
        } elseif { [ module-info shelltype sh ] } {
            puts "unset -f $cmd"
        }
    }
}

# For "module help" and "module load"
if { [ module-info mode help ] || [ module-info mode load ] || [ module-info mode display ] } {
    puts stderr "
\\[ Help information \\]

1. You may use below commands as normal:
$cmds
2. Those commands may only run on computing nodes (not available on head nodes). Make sure you start a job!
"
}
proc ModulesHelp {} {
}
""")
        
        # Return formatted module key string based on the template
        return tmpModKey.safe_substitute(
            modName = modName,
            conflict = dictModule["conflict"],
            whatis = dictModule["module_whatis"],
            modVersion = modVersion,
            singularity_image = dictModule["singularity_image"],
            singularity_bindpaths = dictModule["singularity_bindpaths"],
            singularity_flags = dictModule["singularity_flags"],
            cmds_dummy = dictModule["cmds"],
            envs = envsStr
        )

    #============================================================
    # Misc
    #============================================================
        
    def resizeEnvsColumns(self):
        self.envsTable.setColumnWidth(0, int(0.28*self.envsTable.width()))
        self.envsTable.setColumnWidth(1, int(0.68*self.envsTable.width()))

    def resizeEvent(self, event):
        self.resizeEnvsColumns()
        super().resizeEvent(event)
    
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
        
        # Strip string
        self.modNameText.setText(self.modNameText.text().strip())
        self.modVersionText.setText(self.modVersionText.text().strip())
        
        # Check empty
        if self.modNameText.text().strip() and self.modVersionText.text().strip():
            self.accept() 
        else:
            QMessageBox.warning(self, 'Warning', 'Module name and version cannot be empty!')
        
# Confirmation dialog
class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create text field to enter database name
        self.dbname = QLineEdit(self)
        self.dbname.setText("campDB.json")
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Database name:", self.dbname)

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
        self.msg = QLabel("")
        self.layout.addWidget(QLabel(""))
        self.layout.addWidget(self.msg)
        self.layout.addLayout(self.formLayout)
        self.layout.addWidget(QLabel(""))
        self.layout.addLayout(self.btnLayout)
        self.setLayout(self.layout)
        self.setWindowTitle("Confirm")
    
    def checkEmpty(self):
        
        # Strip string
        self.dbname.setText(self.dbname.text().strip())
        
        # Check empty
        if self.dbname.text():
            self.accept() 
        else:
            QMessageBox.warning(self, 'Warning', 'Database file name name cannot be empty!')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.resizeEnvsColumns()
    mainWindow.dropVersionUpdateFromDB()
    sys.exit(app.exec_())
