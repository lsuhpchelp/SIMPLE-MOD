# =====================================================================
# Containerized App Modulekey Producer (CAMP)
# Developer: Jason Li (jasonli3@lsu.edu)
# Version: 1.0
# Dependency: PyQt5
# =====================================================================


import sys, json, os
from string import Template
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, 
                             QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QDialog, QAction, QFileDialog)

currentModule = {
    "conflict":                 "",
    "module_whatis":            "",
    "singularity_image":        "",
    "singularity_bindpaths":    "",
    "singularity_flags":        "",
    "cmds":                     "",
    "envs":                     {  }
}
db = {}

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
        
        self.flagDBChanged = False
        
        #--------------------------------------------------------
        # Menu bar
        #--------------------------------------------------------
        
        # Menu
        self.menubar = self.menuBar()
        
        # Menu 1
        self.fileMenu = self.menubar.addMenu('\n File ')
        
        self.newDBAct = QAction('New Database', self)
        self.newDBAct.triggered.connect(self.newDB)
        self.newDBAct.setShortcut("Ctrl+N")
        self.fileMenu.addAction(self.newDBAct)
        
        self.openDBAct = QAction('Open Database', self)
        self.openDBAct.triggered.connect(self.openDBDialog)
        self.openDBAct.setShortcut("Ctrl+O")
        self.fileMenu.addAction(self.openDBAct)
        
        self.saveDBAct = QAction('Save Database', self)
        self.saveDBAct.triggered.connect(self.saveDBDialog)
        self.saveDBAct.setShortcut("Ctrl+S")
        self.fileMenu.addAction(self.saveDBAct)
        
        self.fileMenu.addSeparator()
        
        self.exitAct = QAction('Exit', self)
        self.exitAct.triggered.connect(self.close)
        self.exitAct.setShortcut("Alt+F4")
        self.fileMenu.addAction(self.exitAct)

        
        # Menu 2
        self.helpMenu = self.menubar.addMenu(' Help ')

        
        #--------------------------------------------------------
        # Block1: Choose / create module
        #--------------------------------------------------------
        
        # Header
        self.blk1Label = QLabel('Module List')
        self.blk1Label.setStyleSheet('QLabel { font-size: 16px; font-weight: bold; }')
        
        # Module name dropdown menu
        self.nameDrop = QComboBox(self)
        self.nameDrop.currentTextChanged.connect(self.nameDropChanged)
        self.nameDropUpdateFromDB()
        
        # Module version dropdown menu
        self.versionDrop = QComboBox(self)
        self.versionDrop.currentTextChanged.connect(self.versionDropChanged)
        
        # Add / Delete buttons
        self.addBtn = QPushButton("Add a new module", self)
        self.addBtn.clicked.connect(self.addMod)
        self.delBtn = QPushButton("Delete selected module", self)
        self.delBtn.clicked.connect(self.delMod)
        self.blk1BtnLayout = QHBoxLayout()
        self.blk1BtnLayout.addWidget(self.addBtn)
        self.blk1BtnLayout.addWidget(self.delBtn)
        
        # Combine module choose layout
        self.moduleChooseLayout = QFormLayout()
        self.moduleChooseLayout.addRow("Module name", self.nameDrop)
        self.moduleChooseLayout.addRow("Module version", self.versionDrop)
        self.moduleChooseLayout.addRow(self.blk1BtnLayout)
        
        #--------------------------------------------------------
        # Block2: Module details
        #--------------------------------------------------------
        
        # Header
        self.blk2Label = QLabel('Module Details')
        self.blk2Label.setStyleSheet('QLabel { font-size: 16px; font-weight: bold; }')
        
        # Conflicts
        self.conflictText = QLineEdit(self)
        self.conflictText.setPlaceholderText("(Seperate by space. Itself will be added by default.)")
        pal = self.conflictText.palette()
        pal.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#BBBBBB"))
        self.conflictText.setPalette(pal)
        
        # What-is
        self.whatisText = QLineEdit(self)
        
        # Singularity image path (editable text field and file picker button)
        self.singularityImageText = QLineEdit(self)
        self.singularityImagePickerBtn = QPushButton("Browse", self)
        self.singularityImagePickerBtn.clicked.connect(self.pickSingularityImageFile)
        self.singularityImageLayout = QHBoxLayout()
        self.singularityImageLayout.addWidget(self.singularityImageText)
        self.singularityImageLayout.addWidget(self.singularityImagePickerBtn)
        
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
        self.moduleEditLayout.addRow("Software description", self.whatisText)
        self.moduleEditLayout.addRow("Singularity image path", self.singularityImageLayout)
        self.moduleEditLayout.addRow("Singularity binding paths", self.singularityBindText)
        self.moduleEditLayout.addRow("Singularity flags", self.singularityFlagsText)
        self.moduleEditLayout.addRow("Commands to replace", self.cmdsText)
        self.moduleEditLayout.addRow("Set up environmental variable", self.envsTable)
        self.moduleEditLayout.addRow("", self.envsBtnLayout)
        
        #--------------------------------------------------------
        # Block3: Confirmation buttons
        #--------------------------------------------------------
        
        # Add / edit buttons
        self.saveBtn = QPushButton("\nSave to data file\n", self)
        self.saveBtn.clicked.connect(self.saveToFile)
        self.genBtn = QPushButton("\nGenerate current module key\n", self)
        self.genBtn.clicked.connect(self.genModKey)
        self.exportBtn = QPushButton("\nGenerate all keys from data file\n", self)
        self.exportBtn.clicked.connect(self.genAllModKeys)
        self.confirmationBtnsLayout = QHBoxLayout()
        self.confirmationBtnsLayout.addWidget(self.saveBtn)
        self.confirmationBtnsLayout.addWidget(self.genBtn)
        self.confirmationBtnsLayout.addWidget(self.exportBtn)
            
        #--------------------------------------------------------

        # Create main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(QLabel("", self))
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
    # Menu methods
    #============================================================
    
    def newDB(self):
        """
        Create a new empty database.
        """
        
        # Check any unsaved changes
        if (self.stayForUnsavedChanges()): return
        
        # Reset database to empty
        global db, currentModule
        db = {}
        currentModule = {
            "conflict":                 "",
            "module_whatis":            "",
            "singularity_image":        "",
            "singularity_bindpaths":    "",
            "singularity_flags":        "",
            "cmds":                     "",
            "envs":                     {  }
        }
        
        # Update current form
        self.nameDropUpdateFromDB()
        self.versionDropUpdateFromDB()
        
        # Mark database as unchanged
        self.flagDBChanged = False
    
    def openDBDialog(self):
        """
        Select and open database file.
        """
        
        # Check any unsaved changes
        if (self.stayForUnsavedChanges()): return
        
        global db
        
        # Pick a database file to open
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Database', filter="Text Files (*.json)")
        if fname:
        
            # Read to "db" dictionary
            with open(fname) as f:
                db = json.load(f)
                
            # Update currrent form
            self.nameDropUpdateFromDB()
            self.versionDropUpdateFromDB()
        
        # Mark database as unchanged
        self.flagDBChanged = False

    def saveDBDialog(self):
        """
        Select and save database file.
        """
        
        global db
        
        # At least one module (current) must exist, or return error:
        if (self.nameDrop.currentText() and self.nameDrop.currentText()):
        
            # Pick a database file to save
            fname, _ = QFileDialog.getSaveFileName(self, 'Save Database', filter="Text Files (*.json)")
            if fname:
        
                # Add ".json" extension of not already added
                if (fname.split(".")[-1] != "json"):
                    fname += ".json"
                
                # Set currentModule to the values in the fields
                self.modSaveToDB()
            
                # Save changes
                db[self.nameDrop.currentText()][self.versionDrop.currentText()] = currentModule
                with open(fname, "w") as fw:
                    json.dump(db, fw, indent=4)
                
        else:
        
            QMessageBox.warning(self, 'Warning', 'At least one module must exist to save!')
        
        # Mark database as unchanged
        self.flagDBChanged = False

    def selectModKeyPath(self):
        """
        Select path to export module keys.
        """
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory')

        if directory:
            print("Selected directory:", directory)


    #============================================================
    # Dropdown menu methods
    #============================================================

    def nameDropUpdateFromDB(self):
        """
        Update module name dropdown menu.
        """
        self.nameDrop.currentTextChanged.disconnect()
        self.nameDrop.clear()
        self.nameDrop.addItems(sorted(db.keys()))
        self.nameDropCurrentText = self.nameDrop.currentText()
        self.nameDrop.currentTextChanged.connect(self.nameDropChanged)

    def nameDropSetCurrentText(self, text):
        """
        Set (silently) current text for name dropdown menu.
        """
        self.nameDrop.currentTextChanged.disconnect()
        self.nameDrop.setCurrentText(text)
        self.nameDropCurrentText = text
        self.nameDrop.currentTextChanged.connect(self.nameDropChanged)
        
    def nameDropChanged(self, text):
        """
        When selected module name is changed.
        """
        
        # Check any unsaved changes in the current module form
        if (self.stayForUnsavedModChanges()): 
        
            # If choose to stay for unsaved changes, revert all
            self.nameDrop.currentTextChanged.disconnect()
            self.nameDrop.setCurrentText(self.nameDropCurrentText)
            self.nameDrop.currentTextChanged.connect(self.nameDropChanged)
            
        else:
        
            # Otherwise continue, update version dropdown menu
            self.nameDropCurrentText = text
            self.versionDropUpdateFromDB()

    def versionDropUpdateFromDB(self):
        """
        Update module version dropdown menu.
        """
        self.versionDrop.currentTextChanged.disconnect()
        self.versionDrop.clear()
        if (self.nameDrop.currentText()) :
            self.versionDrop.addItems(sorted(db[self.nameDrop.currentText()].keys()))
        self.modUpdateFromDB()
        self.versionDrop.currentTextChanged.connect(self.versionDropChanged)

    def versionDropSetCurrentText(self, text):
        """
        Set (silently) current text for version dropdown menu.
        """
        self.versionDrop.currentTextChanged.disconnect()
        self.versionDrop.setCurrentText(text)
        self.versionDrop = text
        self.versionDrop.currentTextChanged.connect(self.versionDropChanged)
        
    def versionDropChanged(self, text):
        """
        When selected module version is changed.
        """
        
        # Check any unsaved changes
        if (self.stayForUnsavedModChanges()): 
        
            # If choose to stay for unsaved changes, revert all
            self.versionDrop.currentTextChanged.disconnect()
            self.versionDrop.setCurrentText(self.versionDropCurrentText)
            self.versionDrop.currentTextChanged.connect(self.versionDropChanged)
            
        else:
        
            # Otherwise continue, update module form to current selected module
            self.versionDropCurrentText = text
            self.modUpdateFromDB()


    #============================================================
    # Module form methods
    #============================================================
     
    def modUpdateFromDB(self):
        """
        Update module form from database ("currentModule" dictionary)
        """
    
        global currentModule
        
        # If a non-empty module is selected, update currentModule from database and enable all fields;
        # If not, meaning nothing is selected, disable all fields
        if (self.nameDrop.currentText() and self.versionDrop.currentText()) :
            currentModule = db[self.nameDrop.currentText()][self.versionDrop.currentText()]
            self.conflictText.setEnabled(True)
            self.whatisText.setEnabled(True)
            self.singularityImageText.setEnabled(True)
            self.singularityImagePickerBtn.setEnabled(True)
            self.singularityBindText.setEnabled(True)
            self.singularityFlagsText.setEnabled(True)
            self.cmdsText.setEnabled(True)
            self.envsTable.setEnabled(True)
            self.envsAddBtn.setEnabled(True)
            self.envsDelBtn.setEnabled(True)
            self.delBtn.setEnabled(True)
        else:
            self.conflictText.setEnabled(False)
            self.whatisText.setEnabled(False)
            self.singularityImageText.setEnabled(False)
            self.singularityImagePickerBtn.setEnabled(False)
            self.singularityBindText.setEnabled(False)
            self.singularityFlagsText.setEnabled(False)
            self.cmdsText.setEnabled(False)
            self.envsTable.setEnabled(False)
            self.envsAddBtn.setEnabled(False)
            self.envsDelBtn.setEnabled(False)
            self.delBtn.setEnabled(False)
    
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
        
    def pickSingularityImageFile(self):
        """
        Pick Singularity image file in file browser.
        """
        
        # Pick a database file to open
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Singularity image file', filter="Singularity Image (*.sif *.img)")
        if fname:
            self.singularityImageText.setText(fname)
            
    
    #============================================================
    # Add / Delete module
    #============================================================

    def addMod(self):
        """
        Add a module.
        """
        
        # Check any unsaved changes
        if (self.stayForUnsavedModChanges()): return
    
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
            self.nameDropUpdateFromDB()
            self.nameDrop.setCurrentText(newModDial.modNameText.text())
            self.versionDropUpdateFromDB()
            self.versionDrop.setCurrentText(newModDial.modVersionText.text())
            self.modUpdateFromDB()
            
            # Mark database as changed
            self.flagDBChanged = True

    def delMod(self):
        """
        Delete selected module.
        """
        
        # Confirm whether to delete
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to delete this module?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            
            # Check whether this module has multiple versions
            if len(db[self.nameDrop.currentText()].keys()) > 1:
                
                # If so, only delete the selected version
                del db[self.nameDrop.currentText()][self.versionDrop.currentText()]
                
                # Select next available version
                self.versionDropUpdateFromDB()
                
            else:
                
                # If not (this is the only version), delete the entire module entry
                del db[self.nameDrop.currentText()]
                
                # Update the name dropdown menu
                self.nameDropUpdateFromDB()
                self.versionDropUpdateFromDB()
            
            # Mark database as changed
            self.flagDBChanged = True
            

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
     
    def envsTableToDict(self):
        """
        Convert environmental variable table to dictionary and return.
        """
    
        # Clear the current data in currentModule
        ret = {}
        
        # Save current values in the table to dictionary
        for row in range(self.envsTable.rowCount()):
            if self.envsTable.item(row,0) and self.envsTable.item(row,1):
                ret[self.envsTable.item(row,0).text()] = self.envsTable.item(row,1).text()
        
        # Returm
        return(ret)
     
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
    
        # Save current values in the table to dictionary
        currentModule["envs"] = self.envsTableToDict()


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
            pathModKey = f"../modulekey/{self.nameDrop.currentText()}/{self.versionDrop.currentText()}"
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
            
                # First remove all module keys with this name (of different versions)
                #for f in os.listdir(modName):
                #    try:
                #        os.remove(f"../modulekey/{modName}/{f}")
                #    except Exception as e:
                #        print(f'Error occurred while deleting file {f}. Error: {e}')
                
                # Then export all module keys
                for modVersion in db[modName].keys():
                
                    # Create folder if not exist
                    pathModKey = f"../modulekey/{modName}/{modVersion}"
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
        with open("campTmp.tcl") as f:
            tmpModKey = Template(f.read())
        
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
    
    def closeEvent(self, event):
        """
        Exit CAMP.
        """
        # Check any unsaved changes
        if (self.stayForUnsavedChanges()): 
            event.ignore()

    def resizeEnvsColumns(self):
        self.envsTable.setColumnWidth(0, int(0.28*self.envsTable.width()))
        self.envsTable.setColumnWidth(1, int(0.68*self.envsTable.width()))

    def resizeEvent(self, event):
        self.resizeEnvsColumns()
        super().resizeEvent(event)
        
    def isDBChanged(self):
        """
        Check if the database is changed (added / deleted module keys) from creation (new or open)
        """
        return(self.flagDBChanged)
    
    def isModKeyChanged(self):
        """
        Check if the current form (module key) is changed from currentModule
        """
        
        if (currentModule["conflict"] != self.conflictText.text() or \
            currentModule["module_whatis"] != self.whatisText.text() or \
            currentModule["singularity_image"] != self.singularityImageText.text() or \
            currentModule["singularity_bindpaths"] != self.singularityBindText.text() or \
            currentModule["singularity_flags"] != self.singularityFlagsText.text() or \
            currentModule["cmds"] != self.cmdsText.toPlainText() or \
            currentModule["envs"] != self.envsTableToDict() ):
            return(True)
        else:
            return(False)
    
    def stayForUnsavedChanges(self):
        """
        Check if either the database or the current form is changed.
        """
        
        # Only pop a confirmation if there is unsaved changes
        if (self.isDBChanged() or self.isModKeyChanged()):
            
            # Ask the user whether to continue
            reply = QMessageBox.question(self, 'Confirmation', 
                                     "You have unsaved changes! Doing so will disgard all unsaved changes. Are you sure to continue?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            # Only return True if there is unsaved change and choose to remain on the page
            if reply == QMessageBox.No:
                return(True)
    
    def stayForUnsavedModChanges(self):
        """
        Check only if the current form is changed.
        """
        
        # Only pop a confirmation if there is unsaved changes
        if (self.isModKeyChanged()):
            
            # Ask the user whether to continue
            reply = QMessageBox.question(self, 'Confirmation', 
                                     "You have unsaved changes in the form below! Doing so will disgard all unsaved changes. Are you sure to continue?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            # Only return True if there is unsaved change and choose to remain on the page
            if reply == QMessageBox.No:
                return(True)
        
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
    mainWindow.modUpdateFromDB()
    sys.exit(app.exec_())
