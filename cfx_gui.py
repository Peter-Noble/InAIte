import sys
import math
from PySide import QtCore, QtGui
from collections import OrderedDict
import cfx_compileBrain
from cfx_compileBrain import compilebrain

from cfx_nodeEditor import CfxEditor, NODETYPES

# from cfx_propertiesEditor import Properties
import imp
import cfx_propertiesEditor
imp.reload(cfx_propertiesEditor)
Properties = cfx_propertiesEditor.Properties

import threading
from multiprocessing import Process


class NodeButton(QtGui.QPushButton):
    """The button class for adding new nodes"""

    def __init__(self, editor, target):
        QtGui.QPushButton.__init__(self)
        self.editor = editor
        self.setText(target[0])
        self.clicked.connect(lambda: self.editor.addNode(target[1]))


class NodeList(QtGui.QWidget):
    """The list of buttons for adding new nodes"""

    def __init__(self, editor):
        QtGui.QWidget.__init__(self)
        self.editor = editor
        self.box = QtGui.QHBoxLayout()
        for nodetypes in NODETYPES:
            button = NodeButton(editor, nodetypes)
            self.box.addWidget(button)
        self.setLayout(self.box)
        self.setFixedHeight(self.sizeHint().height())


class main(QtGui.QWidget):
    """Contains everything that is shown in the main part of the window"""

    def __init__(self):
        QtGui.QWidget.__init__(self)
        hbox = QtGui.QHBoxLayout(self)

        self.properties = Properties()
        self.CfxEditor = CfxEditor(self.properties.newSelected)
        middle = NodeList(self.CfxEditor)

        splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.CfxEditor)
        splitter.addWidget(middle)
        splitter.addWidget(self.properties)

        hbox.addWidget(splitter)
        self.setLayout(hbox)
        # noinspection PyTypeChecker
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))

        # self.setWindowTitle('QtGui.QSplitter')
        # self.show()

    def onChanged(self, text):
        self.lbl.setText(text)
        self.lbl.adjustSize()


class Window(QtGui.QMainWindow):
    """The window that is displayed. Contains the menues and their
    functionality"""

    def __init__(self, updatesaves, loadbrains):
        QtGui.QMainWindow.__init__(self)

        self.main = main()

        self.updatesaves = updatesaves

        # self.saveslots = {'NNone': "{'edges': [], 'nodes': {}}"}
        # self.saveslots = {}
        self.saveslots = {}
        for b in loadbrains:
            self.saveslots[b.identify+b.dispname] = b.brain

        self.current = None  # index of the currently open tree

        self.setGeometry(1000, 100, 300, 200)

        def saveas(win, func):
            saveto = QtGui.QInputDialog.getText(win, "Save to", "Name")[0]
            savedata = func()
            win.saveslots[saveto] = savedata.__str__()
            win.lastsaved = savedata
            win.current = saveto
            # print(savedata.__str__().replace("\n", "{NEWLINE}"))
            """assemble the save data and send it back to blender"""
            saves = []
            for item in self.saveslots:
                saves.append((item[0], item[1:], self.saveslots[item]))
            saves = tuple(saves)
            self.updatesaves(saves)

        def savedmove(win, func):
            if win.current:
                win.saveslots[win.current] = func().__str__()
            else:
                saveas(win, func)

        def loadfrom(win):
            loadn, use = QtGui.QInputDialog.getItem(win, "Load from",
                                                    "From",
                                                    list(win.saveslots.keys()))
            win.main.CfxEditor.load(eval(win.saveslots[loadn]))
            win.current = loadn

        def reset(win):
            win.main.CfxEditor.resetGraph()
            win.current = None

        def executebrain(win):
            # ONLY TEMPORY until the Blender plugin can do this for itself
            loadn, use = QtGui.QInputDialog.getItem(win, "Load from", "From",
                                                    list(win.saveslots.keys()))
            compilebrain(win.saveslots[loadn]).execute("RANDOM USER ID")
            #  TODO replace the RANDOM USER ID with something that works

        exitAction = QtGui.QAction("&Exit", self)
        exitAction.triggered.connect(self.close)

        resetAction = QtGui.QAction("&Reset", self)
        resetAction.triggered.connect(lambda: reset(self))

        saveAction = QtGui.QAction("&Save", self)

        saveAction.triggered.connect(lambda:
                                     savedmove(self, self.main.CfxEditor.save))

        saveasaction = QtGui.QAction("&Save as", self)
        saveasaction.triggered.connect(lambda:
                                       saveas(self, self.main.CfxEditor.save))

        loadfromaction = QtGui.QAction("&Load from", self)
        loadfromaction.triggered.connect(lambda: loadfrom(self))

        executefromaction = QtGui.QAction("&Execute from", self)
        executefromaction.triggered.connect(lambda: executebrain(self))

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(exitAction)
        fileMenu.addAction(resetAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveasaction)
        fileMenu.addAction(loadfromaction)
        fileMenu.addAction(executefromaction)

        def saveSnippet(win, func):
            textbox = QtGui.QTextEdit()
            textbox.setText(func().__str__())
            self.textbox = textbox
            textbox.show()

        def insertSnippet(win):
            loadn, use = QtGui.QInputDialog.getText(win, "Insert snippet",
                                                    "Snippet")
            win.main.CfxEditor.insert(eval(loadn))

        saveSnippetAction = QtGui.QAction("&Save snippet", self)
        saveSnippetAction.triggered.connect(lambda: saveSnippet(self,
                                            self.main.CfxEditor.saveSnippet))

        insertSnippetAction = QtGui.QAction("&Insert snippet", self)
        insertSnippetAction.triggered.connect(lambda: insertSnippet(self))

        snippetMenu = menubar.addMenu("&Snippet")
        snippetMenu.addAction(saveSnippetAction)
        snippetMenu.addAction(insertSnippetAction)

        self.setCentralWidget(self.main)

        self.show()


def runui(updatesaves, cfx_brains):
    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication([])

    widget = Window(updatesaves, cfx_brains)
    widget.show()

    # sys.exit(app.exec_())


if __name__ == "__main__":
    runui()
