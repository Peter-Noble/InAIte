import sys
import math
from PySide import QtCore, QtGui
from collections import OrderedDict
from cfx_compileBrain import compilebrain

from cfx_nodeEditor import CfxEditor, NODETYPES
from cfx_propertiesEditor import Properties


class NodeButton(QtGui.QPushButton):
    def __init__(self, editor, target):
        QtGui.QPushButton.__init__(self)
        self.editor = editor
        self.setText(target[0])
        self.clicked.connect(lambda: self.editor.addNode(target[1]))
        

class NodeList(QtGui.QWidget):
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

        #self.setWindowTitle('QtGui.QSplitter')
        #self.show()

    def onChanged(self, text):
        self.lbl.setText(text)
        self.lbl.adjustSize()


class window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.main = main()
        
        self.saveslots = {}
        self.current = None #index of the currently open tree

        self.setGeometry(1000, 100, 300, 200)

        def saveas(self, func):
            saveto = QtGui.QInputDialog.getText(self, "Save to", "Name")[0]
            savedata = func()
            self.saveslots[saveto] = savedata.__str__()
            self.lastsaved = savedata
            self.current = saveto
    
        def savedmove(self, func):
            if self.current:
                self.saveslots[self.current] = func().__str__()
            else:
                saveas(self, func)

        def loadfrom(self):
            loadfrom, use = QtGui.QInputDialog.getItem(self, "Load from", "From", list(self.saveslots.keys()))
            self.main.CfxEditor.load(eval(self.saveslots[loadfrom]))
            self.current = loadfrom

        def reset(self):
            self.main.CfxEditor.resetGraph()
            self.current = None

        def executebrain(self):
            loadfrom, use = QtGui.QInputDialog.getItem(self, "Load from", "From", list(self.saveslots.keys()))
            compilebrain(self.saveslots[loadfrom]).execute()

        exitAction = QtGui.QAction("&Exit", self)
        exitAction.triggered.connect(self.close)

        resetAction = QtGui.QAction("&Reset", self)
        resetAction.triggered.connect(lambda: reset(self))

        saveAction = QtGui.QAction("&Save", self)
                
        saveAction.triggered.connect(lambda: savedmove(self, self.main.CfxEditor.save))

        saveasaction = QtGui.QAction("&Save as", self)
        saveasaction.triggered.connect(lambda: saveas(self, self.main.CfxEditor.save))

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

        self.setCentralWidget(self.main)

        self.show()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    widget = window()
    widget.show()

    sys.exit(app.exec_())
