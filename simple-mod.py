# =====================================================================
# SIMPLE-MOD 
#  (Singularity Integrated Module-key Producer for Loadable 
#   Environment MODules)
# Developer: Jason Li (jasonli3@lsu.edu)
# Dependency: PyQt5 or PyQt6
# =====================================================================


import sys, json, os, tempfile, copy
from string import Template

# QT5/6 dual support (prefer QT6)
try:
    from PyQt6 import QtGui
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
                                 QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox,
                                 QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QDialog, QDialogButtonBox, QFileDialog)
    from PyQt6.QtGui import QAction
    PYQT_VERSION = 6
    PlaceholderTextColorRole = QtGui.QPalette.ColorRole.PlaceholderText
except ImportError:
    from PyQt5 import QtGui
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                                 QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox,
                                 QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QDialog, QDialogButtonBox, QAction, QFileDialog)
    PYQT_VERSION = 5
    PlaceholderTextColorRole = QtGui.QPalette.PlaceholderText
    
# Software Information
TITLE = "SIMPLE-MOD "   # Window title
VERSION="1.1.0"         # Version
ABOUT = f"""{TITLE}
(Singularity Integrated Module-key Producer for Loadable Environment MODules)

SIMPLE-MOD is a QT-based GUI tool to automatically generate module keys for easy access of container-based software packages.
            
Version: \t{VERSION}
Author: \tJason Li
Home: \thttps://github.com/lsuhpchelp/SIMPLE-MOD
License: \tMIT License
"""
    
# Main window
class MainWindow(QMainWindow):
    """
    Main window of SIMPLE-MOD.
    
    Architecture:
    - self.db:             The working database dictionary (module name -> version -> module dict).
    - self.dbOriginal:     Deep copy of the database taken at load/save time, used for unsaved changes detection.
    - self.currentModule:  Reference to the currently selected module's dictionary inside self.db.
    - self._updatingForm:  Guard flag to prevent re-entrant saves when formUpdateFromDB() populates fields.
    
    Form-DB synchronization:
        All form field signals (textChanged, itemChanged) are connected to formOnFieldChanged(),
        which calls formSaveToDB() and setTitleForUnsavedChanges() on every edit. This keeps self.db 
        always in sync with the form, so explicit saves before switching modules are not needed.
        
    Naming convention:
        - form*:  Methods related to the module details form (formUpdateFromDB, formSaveToDB, formOnFieldChanged, etc.)
        - mod*:   Methods for module-level CRUD operations (modAdd, modCopy, modDel)
        - envs*:  Methods for the environmental variable table (envsAdd, envsDel, envsUpdateFromDB, etc.)
    """

    #============================================================
    # Constructor
    #============================================================
    def __init__(self):
        """
        Initialize the main window, menu bar, module list panel, module details form,
        and module key generation buttons.
        """
        
        super().__init__()
        
        # Load preferences
        self.loadPreferences()
        
        # Key attributes
        self.db = {}                                # Loaded database dictionary (empty if it's new)
        self.dbOriginal = {}                        # Original copy of database (for unsaved changes detection)
        self.currentModule = self.retEmptyModule()  # Current opened module
        self._updatingForm = False                  # Guard flag to prevent re-entrant saves during form updates
        
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
        
        self.openDBAct = QAction('Open Database...', self)
        self.openDBAct.triggered.connect(self.openDB)
        self.openDBAct.setShortcut("Ctrl+O")
        self.fileMenu.addAction(self.openDBAct)
        
        self.saveDBAct = QAction('Save Database...', self)
        self.saveDBAct.triggered.connect(self.saveDB)
        self.saveDBAct.setShortcut("Ctrl+S")
        self.fileMenu.addAction(self.saveDBAct)
        
        self.fileMenu.addSeparator()
        
        self.exitAct = QAction('Exit', self)
        self.exitAct.triggered.connect(self.close)
        self.exitAct.setShortcut("Alt+F4")
        self.fileMenu.addAction(self.exitAct)

        
        # Menu 2
        self.settingsMenu = self.menubar.addMenu(' Settings ')
        
        self.preferencesAct = QAction('Preferences...', self)
        self.preferencesAct.triggered.connect(self.preferencesDialog)
        self.preferencesAct.setShortcut("Ctrl+P")
        self.settingsMenu.addAction(self.preferencesAct)

        
        # Menu 3
        self.helpMenu = self.menubar.addMenu(' Help ')
        
        self.aboutAct = QAction('About', self)
        self.aboutAct.triggered.connect(self.aboutDialog)
        self.aboutAct.setShortcut("F1")
        self.helpMenu.addAction(self.aboutAct)
        
        self.aboutQTAct = QAction('About QT', self)
        self.aboutQTAct.triggered.connect(self.aboutQtDialog)
        self.helpMenu.addAction(self.aboutQTAct)

        
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
        self.addBtn.clicked.connect(self.modAdd)
        self.copyBtn = QPushButton("Copy current module", self)
        self.copyBtn.clicked.connect(self.modCopy)
        self.delBtn = QPushButton("Delete selected module", self)
        self.delBtn.clicked.connect(self.modDel)
        self.blk1BtnLayout = QHBoxLayout()
        self.blk1BtnLayout.addWidget(self.addBtn)
        self.blk1BtnLayout.addWidget(self.copyBtn)
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
        self.conflictText.setPlaceholderText("(Seperate by space. Itself is already added.)")
        pal = self.conflictText.palette()
        pal.setColor(PlaceholderTextColorRole, QtGui.QColor("#BBBBBB"))
                # Placeholder text color palette. Will be reused.
        self.conflictText.setPalette(pal)
        self.conflictText.textChanged.connect(self.formOnFieldChanged)
        
        # What-is
        self.whatisText = QLineEdit(self)
        self.whatisText.textChanged.connect(self.formOnFieldChanged)
        
        # Singularity image path (editable text field and file picker button)
        self.singularityImageText = QLineEdit(self)
        self.singularityImageText.textChanged.connect(self.formOnFieldChanged)
        self.singularityImagePickerBtn = QPushButton("Browse", self)
        self.singularityImagePickerBtn.clicked.connect(self.formPickSingularityImageFile)
        self.singularityImageLayout = QHBoxLayout()
        self.singularityImageLayout.addWidget(self.singularityImageText)
        self.singularityImageLayout.addWidget(self.singularityImagePickerBtn)
        
        # Singularity binding path
        self.singularityBindText = QLineEdit(self)
        self.singularityBindText.setPlaceholderText(f"(Already bound: /home,/tmp,{self.config['defaultBindingPath']})")
        self.singularityBindText.setPalette(pal)
        self.singularityBindText.textChanged.connect(self.formOnFieldChanged)
        
        # Singularity flags
        self.singularityFlagsText = QLineEdit(self)
        self.singularityFlagsText.setPlaceholderText(f"(Already enabled: {self.config['defaultFlags']})")
        self.singularityFlagsText.setPalette(pal)
        self.singularityFlagsText.textChanged.connect(self.formOnFieldChanged)
        
        # Commands to replace
        self.cmdsText = QTextEdit(self)
        self.cmdsText.setPlaceholderText("(Seperate by space or new line)")
        self.cmdsText.setPalette(pal)
        self.cmdsText.textChanged.connect(self.formOnFieldChanged)
        
        # Environment variables to set up
        self.envsTable = QTableWidget(1, 2, self)
        self.envsUpdateFromDB()
        self.envsTable.itemChanged.connect(self.formOnFieldChanged)
        
        # Environment variables add / delete entry
        self.envsAddBtn =  QPushButton("Add", self)
        self.envsAddBtn.clicked.connect(self.envsAdd)
        self.envsDelBtn =  QPushButton("Delete", self)
        self.envsDelBtn.clicked.connect(self.envsDel)
        self.envsBtnLayout = QHBoxLayout()
        self.envsBtnLayout.addWidget(self.envsAddBtn)
        self.envsBtnLayout.addWidget(self.envsDelBtn)
        
        # Template file path (editable text field and file picker button)
        self.templateText = QLineEdit(self)
        self.templateText.textChanged.connect(self.formOnFieldChanged)
        self.templatePickerBtn = QPushButton("Browse", self)
        self.templatePickerBtn.clicked.connect(self.formPickTemplate)
        self.templateLayout = QHBoxLayout()
        self.templateLayout.addWidget(self.templateText)
        self.templateLayout.addWidget(self.templatePickerBtn)
        
        # Combine module edit layout
        self.moduleEditLayout = QFormLayout()
        self.moduleEditLayout.addRow("Conflicts", self.conflictText)
        self.moduleEditLayout.addRow("Software description", self.whatisText)
        self.moduleEditLayout.addRow("Singularity image path", self.singularityImageLayout)
        self.moduleEditLayout.addRow("Singularity binding paths", self.singularityBindText)
        self.moduleEditLayout.addRow("Additional Singularity flags", self.singularityFlagsText)
        self.moduleEditLayout.addRow("Commands to map", self.cmdsText)
        self.moduleEditLayout.addRow("Set up environmental variable", self.envsTable)
        self.moduleEditLayout.addRow("", self.envsBtnLayout)
        self.moduleEditLayout.addRow("Module key template", self.templateLayout)
        
        #--------------------------------------------------------
        # Block3: Confirmation buttons
        #--------------------------------------------------------
        
        # Add / edit buttons
        self.genBtn = QPushButton("\nGenerate current module key\n", self)
        self.genBtn.clicked.connect(self.genModKey)
        self.exportBtn = QPushButton("\nGenerate all module keys from current database\n", self)
        self.exportBtn.clicked.connect(self.genAllModKeys)
        self.confirmationBtnsLayout = QHBoxLayout()
        self.confirmationBtnsLayout.addWidget(self.genBtn)
        self.confirmationBtnsLayout.addWidget(self.exportBtn)
            
        #--------------------------------------------------------
        # Combine all to create main window
        #--------------------------------------------------------

        # Create main layout
        self.mainLayout = QVBoxLayout()
        #self.mainLayout.addWidget(QLabel("", self))
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
        self.setWindowTitle(TITLE)
        self.setGeometry(100, 100, 750, 750)
    
    
    #============================================================
    # Menu methods
    #============================================================
    
    def newDB(self):
        """
        Create a new empty database.
        """
        
        # Check any unsaved changes
        if (self.cancelForUnsavedChanges()): return
        
        # Reset database to empty
        self.db = {}
        self.currentModule = self.retEmptyModule()
        
        # Update current form
        self.nameDropUpdateFromDB()
        self.versionDropUpdateFromDB()
        
        # Save original copy of database
        self.dbOriginal = copy.deepcopy(self.db)
        
        # Update window title
        self.setTitleForUnsavedChanges()
    
    def openDB(self):
        """
        Select and open database file.
        """
        
        # Check any unsaved changes
        if (self.cancelForUnsavedChanges()): return
        
        # Pick a database file to open
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Database', "database/", filter="JSON Files (*.json)")
        
        # If successfully picked a file...
        if fname:
            
            # Try if this file is writable:
            # If writable, continue saving; if not, return False
            try:
                f = open(fname)
            except:
                QMessageBox.critical(self, 'Error!', 'You cannot read this file!')
                return(False)
        
            # Read to "db" dictionary
            self.db = json.load(f)
            f.close()
                
            # Update currrent form
            self.nameDropUpdateFromDB()
            self.versionDropUpdateFromDB()
            
            # Save original copy of database
            self.dbOriginal = copy.deepcopy(self.db)
        
            # Update window title
            self.setTitleForUnsavedChanges()

    def saveDB(self):
        """
        Save database to file. To avoid data loss, always ask for confirmation.
        Return:
            True:   Successfully saved
            False:  Not saved
        """
        
        # At least one module (current) must exist, or return error:
        if (self.nameDrop.currentText() and self.nameDrop.currentText()):
            
            # Pick a database file to save
            fname, _ = QFileDialog.getSaveFileName(self, 'Save Database', "database/", filter="JSON Files (*.json)")
                
            # If successfully picked a file...
            if fname:
        
                # Add ".json" extension of not already added
                if (fname.split(".")[-1] != "json"):
                    fname += ".json"
            
                # Try if this file is writable:
                # If writable, continue saving; if not, return False
                try:
                    fw = open(fname, "w")
                except:
                    QMessageBox.critical(self, 'Error!', 'Saving failed! You do not have permission to write to this file!')
                    return(False)
                
                # Save currentModule to database
                self.db[self.nameDrop.currentText()][self.versionDrop.currentText()] = self.currentModule
                
                # Save database to file
                json.dump(self.db, fw, indent=4)
                fw.close()
        
                # Save original copy of database
                self.dbOriginal = copy.deepcopy(self.db)
        
                # Update window title
                self.setTitleForUnsavedChanges()
                
                # Return successful
                return(True)
                
        else:
        
            QMessageBox.critical(self, 'Error!', 'At least one module must exist to save!')
        
        # If has not successfully returned at this point, return False
        return(False)

    def preferencesDialog(self):
        """
        Open the Preferences dialog to edit default settings (binding paths, flags, 
        image path, template, and module key output path). Saves to ~/.simple-modrc on confirm.
        """
        
        # Open a dialog
        prefDial = PreferenceDialog(self)
        
        # If confirmed, save preferences
        if prefDial.exec():
            
            # Save preferences to self.config
            self.config["defaultBindingPath"] = prefDial.defaultBindingPathText.text()
            self.config["defaultFlags"] = prefDial.defaultFlagsText.text()
            self.config["defaultImagePath"] = prefDial.defaultImagePathText.text()
            self.config["defaultTemplate"] = prefDial.defaultTemplateText.text()
            self.config["defaultModKeyPath"] = prefDial.defaultModKeyPathText.text()
        
            # Write to configuration file
            with open(os.path.expanduser('~/.simple-modrc'), "w") as fw:
                json.dump(self.config, fw, indent=4)
            
            # Update prompts
            self.singularityBindText.setPlaceholderText(f"(Already bound: /home,/tmp,{self.config['defaultBindingPath']})")
            self.singularityFlagsText.setPlaceholderText(f"(Already enabled: {self.config['defaultFlags']})")
            

    def aboutDialog(self):
        """
        Show the About SIMPLE-MOD dialog.
        """
        QMessageBox.about(self, "About", ABOUT)

    def aboutQtDialog(self):
        """
        Show the About QT dialog.
        """
        
        QMessageBox.aboutQt(self, "About QT")


    #============================================================
    # Dropdown menu methods
    #============================================================

    def nameDropUpdateFromDB(self):
        """
        Update the module name dropdown menu from self.db keys.
        Temporarily disconnects the change signal to prevent triggering nameDropChanged.
        """
        self.nameDrop.currentTextChanged.disconnect()
        self.nameDrop.clear()
        self.nameDrop.addItems(sorted(self.db.keys()))
        self.nameDropCurrentText = self.nameDrop.currentText()
        self.nameDrop.currentTextChanged.connect(self.nameDropChanged)

    def nameDropSetCurrentText(self, text):
        """
        Set the current text for the name dropdown without triggering nameDropChanged.
        """
        self.nameDrop.currentTextChanged.disconnect()
        self.nameDrop.setCurrentText(text)
        self.nameDropCurrentText = text
        self.nameDrop.currentTextChanged.connect(self.nameDropChanged)
        
    def nameDropChanged(self, text):
        """
        Slot for when the selected module name changes. Updates the version dropdown
        to list versions of the newly selected module.
        """
        
        # Continue, update version dropdown menu
        self.nameDropCurrentText = text
        self.versionDropUpdateFromDB()

    def versionDropUpdateFromDB(self):
        """
        Update the module version dropdown menu from self.db for the currently selected module name.
        Temporarily disconnects the change signal to prevent triggering versionDropChanged.
        Also calls formUpdateFromDB() to refresh the form.
        """
        self.versionDrop.currentTextChanged.disconnect()
        self.versionDrop.clear()
        if (self.nameDrop.currentText()) :
            self.versionDrop.addItems(sorted(self.db[self.nameDrop.currentText()].keys(), reverse=True))
        self.formUpdateFromDB()
        self.versionDrop.currentTextChanged.connect(self.versionDropChanged)

    def versionDropSetCurrentText(self, text):
        """
        Set the current text for the version dropdown without triggering versionDropChanged.
        """
        self.versionDrop.currentTextChanged.disconnect()
        self.versionDrop.setCurrentText(text)
        self.versionDropCurrentText = text
        self.versionDrop.currentTextChanged.connect(self.versionDropChanged)
        
    def versionDropChanged(self, text):
        """
        Slot for when the selected module version changes.
        Calls formUpdateFromDB() to load the newly selected module into the form.
        """
        
        # Continue, update module form to current selected module
        self.versionDropCurrentText = text
        self.formUpdateFromDB()


    #============================================================
    # Module form methods
    #============================================================
     
    def formUpdateFromDB(self):
        """
        Populate the module details form from the currently selected module in self.db.
        Sets self._updatingForm to True during the update to prevent formOnFieldChanged()
        from writing partially loaded data back to the database.
        """
    
        # Guard against re-entrant saves during form updates
        self._updatingForm = True
        
        # If a non-empty module is selected, update currentModule from database and enable all fields;
        # If not, meaning nothing is selected, disable all fields
        if (self.nameDrop.currentText() and self.versionDrop.currentText()) :
            self.currentModule = self.db[self.nameDrop.currentText()][self.versionDrop.currentText()]
            self.enableForm(True)
        else:
            self.enableForm(False)
    
        # Set all values from currentModule dict
        self.conflictText.setText(self.currentModule["conflict"])
        self.whatisText.setText(self.currentModule["module_whatis"])
        self.singularityImageText.setText(self.currentModule["singularity_image"])
        self.singularityBindText.setText(self.currentModule["singularity_bindpaths"])
        self.singularityFlagsText.setText(self.currentModule["singularity_flags"])
        self.cmdsText.setText(self.currentModule["cmds"])
        self.envsUpdateFromDB()
        self.templateText.setText(self.currentModule["template"])
        
        # Release guard and update window title
        self._updatingForm = False
        self.setTitleForUnsavedChanges()
     
    def formSaveToDB(self):
        """
        Save all form field values into the self.currentModule dictionary,
        which is a reference inside self.db. This keeps the database in sync with the form.
        """
        
        # Save all values to currentModule dict
        self.currentModule["conflict"] = self.conflictText.text()
        self.currentModule["module_whatis"] = self.whatisText.text()
        self.currentModule["singularity_image"] = self.singularityImageText.text()
        self.currentModule["singularity_bindpaths"] = self.singularityBindText.text()
        self.currentModule["singularity_flags"] = self.singularityFlagsText.text()
        self.currentModule["cmds"] = self.cmdsText.toPlainText()
        self.envsSaveToDB()
        self.currentModule["template"] = self.templateText.text()
    
    def formOnFieldChanged(self):
        """
        Slot connected to all form field change signals (textChanged, itemChanged).
        Saves the form to self.db via formSaveToDB() and updates the window title
        to reflect unsaved changes. Skipped when self._updatingForm is True (i.e.,
        during formUpdateFromDB()) to avoid writing back partially loaded data.
        """
        
        if self._updatingForm:
            return
        self.formSaveToDB()
        self.setTitleForUnsavedChanges()
        
    def formPickSingularityImageFile(self):
        """
        Open a file browser to pick a Singularity image file (.sif or .img)
        and set it in the Singularity image path field.
        """
        
        # Pick a database file to open
        fname, _ = QFileDialog.getOpenFileName(self, 'Choose Singularity Image File', self.config["defaultImagePath"], filter="Singularity Image (*.sif *.img)")
        if fname:
            self.singularityImageText.setText(fname)
        
    def formPickTemplate(self):
        """
        Open a file browser to pick a module key template file
        and set it in the template path field.
        """
        
        # Pick a database file to open
        fname, _ = QFileDialog.getOpenFileName(self, 'Choose Module Key Template File', "template", filter="All files (*)")
        if fname:
            self.templateText.setText(fname)
            
    
    #============================================================
    # Add / Delete module
    #============================================================

    def modAdd(self):
        """
        Open a dialog to add a new module. Creates a new empty module entry in self.db
        and switches the form to the newly created module.
        """
    
        # Open a dialog
        newModDial = NewModuleDialog(self)
        
        # If confirmed, create module
        if newModDial.exec():

            # Strip module name and version
            modName = newModDial.modNameText.text()
            modVersion = newModDial.modVersionText.text()
            
            # Check a module with the same name already exist:
            if (modName in self.db.keys()):
            
                # If the module of the same name and version exists, warn and do nother
                if (modVersion in self.db[modName].keys()):
                    QMessageBox.critical(self, 'Error', 'Module of the same name and version already exists!')
                    return
                    
                else:
                
                    # If the module name is found but version is not, add a new version to existing module name
                    self.db[modName][modVersion] = self.retEmptyModule()
                    
            else:
            
                # If the module name is not found, add a new module name
                self.db[modName] = { 
                    modVersion : self.retEmptyModule()
                }
                
            # Update dropdown menu
            self.nameDropUpdateFromDB()
            self.nameDropSetCurrentText(newModDial.modNameText.text())
            self.versionDropUpdateFromDB()
            self.versionDropSetCurrentText(newModDial.modVersionText.text())
            self.formUpdateFromDB()
        
            # Update window title
            self.setTitleForUnsavedChanges()

    def modCopy(self):
        """
        Open a dialog to copy the current module under a new name/version.
        Creates a copy of self.currentModule in self.db and switches the form to the copy.
        """
    
        # Open a dialog
        newModDial = NewModuleDialog(self)
        
        # If confirmed, create module
        if newModDial.exec():

            # Strip module name and version
            modName = newModDial.modNameText.text()
            modVersion = newModDial.modVersionText.text()
            
            # Check a module with the same name already exist:
            if (modName in self.db.keys()):
            
                # If the module of the same name and version exists, warn and do nother
                if (modVersion in self.db[modName].keys()):
                    QMessageBox.critical(self, 'Error', 'Module of the same name and version already exists!')
                    return
                    
                else:
                
                    # If the module name is found but version is not, add a new version to existing module name
                    self.db[modName][modVersion] = self.currentModule.copy()
                    
            else:
            
                # If the module name is not found, add a new module name
                self.db[modName] = { 
                    modVersion : self.currentModule.copy()
                }
                
            # Update dropdown menu
            self.nameDropUpdateFromDB()
            self.nameDropSetCurrentText(newModDial.modNameText.text())
            self.versionDropUpdateFromDB()
            self.versionDropSetCurrentText(newModDial.modVersionText.text())
            self.formUpdateFromDB()
        
            # Update window title
            self.setTitleForUnsavedChanges()

    def modDel(self):
        """
        Delete the currently selected module after user confirmation.
        If the module has multiple versions, only the selected version is deleted;
        otherwise, the entire module entry is removed from self.db.
        """
        
        # Confirm whether to delete
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to delete this module? This change cannot be reverted!", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            
            # Check whether this module has multiple versions
            if len(self.db[self.nameDrop.currentText()].keys()) > 1:
                
                # If so, only delete the selected version
                del self.db[self.nameDrop.currentText()][self.versionDrop.currentText()]
                
                # Select next available version
                self.versionDropUpdateFromDB()
                
            else:
                
                # If not (this is the only version), delete the entire module entry
                del self.db[self.nameDrop.currentText()]
                
                # Update the name dropdown menu
                self.nameDropUpdateFromDB()
                self.versionDropUpdateFromDB()
            
            # Update window title
            self.setTitleForUnsavedChanges()
            

    #============================================================
    # Environment variable table related methods
    #============================================================

    def envsAdd(self):
        """
        Add a new row to the environmental variable table with a default name.
        """
        self.envsTable.setRowCount(self.envsTable.rowCount()+1)
        item = QTableWidgetItem(f"ENV_{self.envsTable.rowCount()}")
        self.envsTable.setItem(self.envsTable.rowCount()-1, 0, item)
        item = QTableWidgetItem("")
        self.envsTable.setItem(self.envsTable.rowCount()-1, 1, item)

    def envsDel(self):
        """
        Delete the selected row(s) from the environmental variable table.
        Manually calls formOnFieldChanged() because the table's itemChanged signal
        is not emitted on row deletion.
        """
        items = self.envsTable.selectedItems()
        for item in items:
            self.envsTable.removeRow(item.row())
        
        # Manually update because "itemChanged" signal is not triggered at deletion
        self.formOnFieldChanged()
     
    def envsTableToDict(self):
        """
        Convert the environmental variable table contents to a dictionary and return it.
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
        Populate the environmental variable table from self.currentModule["envs"].
        """
        
        # Clear current values
        self.envsTable.clear()
        
        # Reset table
        keys = list(self.currentModule["envs"].keys())
        self.envsTable.setHorizontalHeaderLabels(["Name", "Value"])
        self.envsTable.setRowCount(len(keys))
        
        # Add new entries
        for row in range(len(keys)):
            item = QTableWidgetItem(keys[row])
            self.envsTable.setItem(row, 0, item)
            item = QTableWidgetItem(self.currentModule["envs"][keys[row]])
            self.envsTable.setItem(row, 1, item)
     
    def envsSaveToDB(self):
        """
        Save the environmental variable table contents into self.currentModule["envs"].
        """
    
        # Save current values in the table to dictionary
        self.currentModule["envs"] = self.envsTableToDict()


    #============================================================
    # Execution buttons methods
    #============================================================

    def genModKey(self):
        """
        Generate a module key file for the currently displayed form contents.
        Reads directly from the form fields so saving is not required.
        Prompts the user to select an output directory.
        """
        
        # Asked the user to select a directory
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory to Save Module Keys', self.config["defaultModKeyPath"])

        # If a directory is successfully selected...
        if directory:
            
            # Try if the directory is writable:
            # If writable, continue generating; if not, return False
            try:
                fw = tempfile.TemporaryFile(dir=directory)
            except:
                QMessageBox.critical(self, 'Error!', 'Failed! You do not have permission to write to this directory!')
                return(False)
                    
            # Save a temporary module dict (allows exporting current module without saving)
            tmpModule = {
                "conflict":                 self.conflictText.text(),
                "module_whatis":            self.whatisText.text(),
                "singularity_image":        self.singularityImageText.text(),
                "singularity_bindpaths":    self.singularityBindText.text(),
                "singularity_flags":        self.singularityFlagsText.text(),
                "cmds":                     self.cmdsText.toPlainText(),
                "envs":                     self.envsTableToDict(),
                "template":                 self.templateText.text()
            }
            
            # Create folder if not exist
            pathModKey = f"{directory}/{self.nameDrop.currentText()}/{self.versionDrop.currentText()}"
            dir = os.path.dirname(pathModKey)
            if not os.path.exists(dir):
                os.makedirs(dir)
            
            # Export module file
            with open(pathModKey, "w") as fw:
                fw.write(self.retModKey(dictModule=tmpModule))
            
            # Pop a successful message
            QMessageBox.information(self, 'Success!', 'You have successfully generated the current module key!')

    def genAllModKeys(self):
        """
        Generate module key files for all modules in the current database.
        The database must be saved first (prompts for unsaved changes).
        Prompts the user to select an output directory.
        """
        
        # Check any unsaved changes
        if (self.cancelForUnsavedChanges()): return
        
        # Asked the user to select a directory
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory to Save Module Keys', self.config["defaultModKeyPath"])

        # If a directory is successfully selected...
        if directory:
            
            # Try if the directory is writable:
            # If writable, continue generating; if not, return False
            try:
                fw = tempfile.TemporaryFile(dir=directory)
            except:
                QMessageBox.critical(self, 'Error!', 'Failed! You do not have permission to write to this directory!')
                return(False)
                
            # Loop over all modules in db to create module keys
            for modName in self.db.keys():
                
                # Then export all module keys
                for modVersion in self.db[modName].keys():
                
                    # Create folder if not exist
                    pathModKey = f"{directory}/{modName}/{modVersion}"
                    dir = os.path.dirname(pathModKey)
                    if not os.path.exists(dir):
                        os.makedirs(dir)
            
                    # Export module file
                    with open(pathModKey, "w") as fw:
                        fw.write(self.retModKey(modName, modVersion, self.db[modName][modVersion]))
            
            # Pop a successful message
            QMessageBox.information(self, 'Success!', 'You have successfully generated all module keys from the current database!')
        

    #============================================================
    # Module key template
    #============================================================

    def retModKey(self, modName=None , modVersion=None, dictModule=None):
        """
        Return a formatted module key string by substituting module values into a template.
        
        Args:
            modName:     Module name (defaults to currently selected name).
            modVersion:  Module version (defaults to currently selected version).
            dictModule:  Module dictionary (defaults to self.currentModule).
        """
        
        # Default module name, version, and module dictionary to current if not given
        modName = modName or self.nameDrop.currentText()
        modVersion = modVersion or self.versionDrop.currentText()
        dictModule = dictModule or self.currentModule
    
        # Parse environmental variable dictionary into a single string
        envsStr = ""
        for key, value in dictModule["envs"].items():
            envsStr += f"setenv {key} \"{value}\"\n"
        
        # Set up module key template
        with open(dictModule["template"]) as f:
            tmpModKey = Template(f.read())
        
        # Return formatted module key string based on the template
        return tmpModKey.safe_substitute(
            modName = modName,
            #modNameCap = modName.upper(),
            conflict = dictModule["conflict"],
            whatis = dictModule["module_whatis"],
            modVersion = modVersion,
            singularity_image = dictModule["singularity_image"],
            singularity_bindpaths = ",".join((self.config["defaultBindingPath"], dictModule["singularity_bindpaths"])),
            singularity_flags = " ".join((self.config["defaultFlags"], dictModule["singularity_flags"])),
            cmds_dummy = dictModule["cmds"],
            envs = envsStr
        )


    #============================================================
    # Misc
    #============================================================
    
    def loadPreferences(self):
        """
        Load preferences from "~/.simple-modrc". Create the file if it does not exist.
        """
        
        # Check if "~/.simple-modrc" exist. 
        #   If exists, open and read preference settings.
        #   If not, create it with default settings.
        if os.path.exists(os.path.expanduser('~/.simple-modrc')):
            with open(os.path.expanduser('~/.simple-modrc')) as f:
                self.config = json.load(f)
        else:
            self.config = {
                "defaultBindingPath": "/work,/project,/usr/local/packages,/var/scratch",
                "defaultFlags": "",
                "defaultImagePath": "",
                "defaultTemplate": "./template/template.tcl",
                "defaultModKeyPath": "./modulekey"
            }
            with open(os.path.expanduser('~/.simple-modrc'), "w") as fw:
                json.dump(self.config, fw, indent=4)
                
    def retEmptyModule(self):
        """
        Return an empty module dictionary.
        """
        return {
            "conflict":                 "",
            "module_whatis":            "",
            "singularity_image":        "",
            "singularity_bindpaths":    "",
            "singularity_flags":        "",
            "cmds":                     "",
            "envs":                     {  },
            "template":                 self.config["defaultTemplate"]
        }
    
    def closeEvent(self, event):
        """
        Handle window close event. Prompts for unsaved changes before exiting.
        """
        # Check any unsaved changes
        if (self.cancelForUnsavedChanges()): 
            event.ignore()

    def resizeEnvsColumns(self):
        self.envsTable.setColumnWidth(0, int(0.28*self.envsTable.width()))
        self.envsTable.setColumnWidth(1, int(0.68*self.envsTable.width()))

    def resizeEvent(self, event):
        self.resizeEnvsColumns()
        super().resizeEvent(event)
    
    def enableForm(self, isEnabled):
        """
        Enable/Disable current module form.
        """
        self.saveDBAct.setEnabled(isEnabled)
        self.conflictText.setEnabled(isEnabled)
        self.whatisText.setEnabled(isEnabled)
        self.singularityImageText.setEnabled(isEnabled)
        self.singularityImagePickerBtn.setEnabled(isEnabled)
        self.singularityBindText.setEnabled(isEnabled)
        self.singularityFlagsText.setEnabled(isEnabled)
        self.cmdsText.setEnabled(isEnabled)
        self.envsTable.setEnabled(isEnabled)
        self.envsAddBtn.setEnabled(isEnabled)
        self.envsDelBtn.setEnabled(isEnabled)
        self.templateText.setEnabled(isEnabled)
        self.templatePickerBtn.setEnabled(isEnabled)
        self.copyBtn.setEnabled(isEnabled)
        self.delBtn.setEnabled(isEnabled)
        self.genBtn.setEnabled(isEnabled)
        self.exportBtn.setEnabled(isEnabled)
        
    def hasUnsavedChanges(self):
        """
        Check if there are unsaved changes by comparing self.db with self.dbOriginal.
        Since formOnFieldChanged() keeps self.db in sync with the form at all times,
        this comparison is sufficient to detect any pending changes.
        """
        return self.db != self.dbOriginal
            
    def setTitleForUnsavedChanges(self):
        """
        Every time an unsaved change is present, add a "*" in front of the window title.
        """
        
        if (self.hasUnsavedChanges()):
            self.setWindowTitle("*" + TITLE)
        else:
            self.setWindowTitle(TITLE)
    
    def cancelForUnsavedChanges(self):
        """
        If the database has unsaved changes, prompt the user to save, discard, or cancel.
        
        Returns:
            True:   User chose to cancel, or save failed (caller should abort).
            False:  User chose to continue (with or without saving).
            None:   No unsaved changes detected (caller should continue).
        """
        
        # Only pop a confirmation if there are unsaved changes
        if (self.hasUnsavedChanges()):
            
            # Ask the user whether to continue
            reply = QMessageBox.question(self, 'Confirmation', 
                                     "You have unsaved changes! To avoid data loss, do you want to save the before continue?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
            
            # Depending on the response:
            #   "Yes":      Run "saveDB" method and continue
            #   "No":       Do not save and continue
            #   "Cancel":   Do not save and stay
            if reply == QMessageBox.StandardButton.Yes:
                # Return False (continue) if successfully saved, otherwise return True to stay
                if (self.saveDB()):
                    return(False)
                else:
                    return(True)
            elif reply == QMessageBox.StandardButton.No:
                return(False)
            else:
                return(True)


# New module dialog class
class NewModuleDialog(QDialog):
    """
    Dialog for entering a new module's name and version, used by modAdd() and modCopy().
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create form layout
        self.formLayout = QFormLayout()
        
        # Create text field to enter module name and versions
        self.modNameText = QLineEdit(self)
        self.formLayout.addRow("Module name:", self.modNameText)
        self.modVersionText = QLineEdit(self)
        self.formLayout.addRow("Module version:", self.modVersionText)

        # Create "Save" and "Cancel" buttons
        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.btns.accepted.connect(self.checkEmpty)
        self.btns.rejected.connect(self.reject)
        self.btns.setCenterButtons(True)
        
        # Create entire layout
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.formLayout)
        self.layout.addWidget(self.btns)
        self.setLayout(self.layout)
        self.setWindowTitle("Add a new module")
    
    def checkEmpty(self):
        """
        Check if either module name or version is empty.
        """
        
        # Strip string
        self.modNameText.setText(self.modNameText.text().strip())
        self.modVersionText.setText(self.modVersionText.text().strip())
        
        # Check empty
        if self.modNameText.text().strip() and self.modVersionText.text().strip():
            self.accept() 
        else:
            QMessageBox.critical(self, 'Error', 'Module name and version cannot be empty!')


# Preference dialog class
class PreferenceDialog(QDialog):
    """
    Dialog for editing SIMPLE-MOD preferences (default paths, flags, template).
    Settings are saved to ~/.simple-modrc as JSON.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create form layout
        self.formLayout = QFormLayout()
        
        # Set default binding paths
        self.defaultBindingPathText = QLineEdit(self)
        self.defaultBindingPathText.setText(parent.config["defaultBindingPath"])
        self.formLayout.addRow("Always bind these paths: ", self.defaultBindingPathText)
        
        # Set default flags
        self.defaultFlagsText = QLineEdit(self)
        self.defaultFlagsText.setText(parent.config["defaultFlags"])
        self.formLayout.addRow("Always enable these flags:", self.defaultFlagsText)
        
        # Set default image directory (editable text field and file picker button)
        self.defaultImagePathText = QLineEdit(self)
        self.defaultImagePathText.setText(parent.config["defaultImagePath"])
        self.defaultImagePathPickerBtn = QPushButton("Browse", self)
        self.defaultImagePathPickerBtn.clicked.connect(self.pickDefaultImagePath)
        self.defaultImagePathLayout = QHBoxLayout()
        self.defaultImagePathLayout.addWidget(self.defaultImagePathText)
        self.defaultImagePathLayout.addWidget(self.defaultImagePathPickerBtn)
        self.formLayout.addRow("Default Singularity images directory:", self.defaultImagePathLayout)
        
        # Set default module template (editable text field and file picker button)
        self.defaultTemplateText = QLineEdit(self)
        self.defaultTemplateText.setText(parent.config["defaultTemplate"])
        self.defaultTemplatePickerBtn = QPushButton("Browse", self)
        self.defaultTemplatePickerBtn.clicked.connect(self.pickDefaultTemplate)
        self.defaultTemplateLayout = QHBoxLayout()
        self.defaultTemplateLayout.addWidget(self.defaultTemplateText)
        self.defaultTemplateLayout.addWidget(self.defaultTemplatePickerBtn)
        self.formLayout.addRow("Default module template:", self.defaultTemplateLayout)
        
        # Set default module key generation path (editable text field and file picker button)
        self.defaultModKeyPathText = QLineEdit(self)
        self.defaultModKeyPathText.setText(parent.config["defaultModKeyPath"])
        self.defaultModKeyPathPickerBtn = QPushButton("Browse", self)
        self.defaultModKeyPathPickerBtn.clicked.connect(self.pickDefaultModKeyPath)
        self.defaultModKeyPathLayout = QHBoxLayout()
        self.defaultModKeyPathLayout.addWidget(self.defaultModKeyPathText)
        self.defaultModKeyPathLayout.addWidget(self.defaultModKeyPathPickerBtn)
        self.formLayout.addRow("Default directory to generate module keys:", self.defaultModKeyPathLayout)

        # Create "Save" and "Cancel" buttons
        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        self.btns.setCenterButtons(True)
        
        # Create entire layout
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.formLayout)
        self.layout.addWidget(self.btns)
        self.setLayout(self.layout)
        self.setWindowTitle("Preferences")
        self.resize(600, self.size().height())
    
    def pickDefaultImagePath(self):
        """
        Pick default Singularity path in file browser.
        """
        
        # Pick a directory
        directory = QFileDialog.getExistingDirectory(self, 'Select Default Singularity Image Directory', self.defaultImagePathText.text().strip())
        if directory:
            self.defaultImagePathText.setText(directory)
    
    def pickDefaultTemplate(self):
        """
        Pick default module template in file browser.
        """
        
        # Pick a file
        fname, _ = QFileDialog.getOpenFileName(self, 'Choose Default Module Key Template File', self.defaultTemplateText.text().strip(), filter="All files (*)")
        if fname:
            self.defaultTemplateText.setText(fname)
    
    def pickDefaultModKeyPath(self):
        """
        Pick default default module key generation path in file browser.
        """
        
        # Pick a directory
        directory = QFileDialog.getExistingDirectory(self, 'Select Default Directory to Generate Module Keys', self.defaultModKeyPathText.text().strip())
        if directory:
            self.defaultModKeyPathText.setText(directory)

# Main function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.resizeEnvsColumns()
    mainWindow.formUpdateFromDB()
    sys.exit(app.exec())
