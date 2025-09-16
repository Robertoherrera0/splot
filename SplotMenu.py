from PySide6.QtWidgets import QAction, QFileDialog
from pyspec.css_logger import log
from gans_control.backend.session.spec_session import spec_controller

class CustomMenu:
    def __init__(self, main_window):
        self.main = main_window

    def createMenu(self, menubar_set):
        # New action: create new SPEC datafile
        self.newFileAction = QAction("New Datafile", self.main)
        self.newFileAction.triggered.connect(self.new_datafile)

        # New action: change current datafile
        self.changeFileAction = QAction("Change Datafile", self.main)
        self.changeFileAction.triggered.connect(self.change_datafile)

        # Add to File menu (or a new submenu if you prefer)
        menubar_set.fileMenu.addSeparator()
        menubar_set.fileMenu.addAction(self.newFileAction)
        menubar_set.fileMenu.addAction(self.changeFileAction)

    def new_datafile(self):
        path, _ = QFileDialog.getSaveFileName(self.main, "Create new SPEC datafile")
        if path:
            spec_controller.send(f'newfile -c "{path}" 0')
            self.main.openFile(path, fromSpec=True)

    def change_datafile(self):
        path, _ = QFileDialog.getOpenFileName(self.main, "Select SPEC datafile")
        if path:
            spec_controller.send(f'newfile -c "{path}" 0')
            self.main.openFile(path, fromSpec=True)
