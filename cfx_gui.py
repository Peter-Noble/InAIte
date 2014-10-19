import sys
import math
from PySide import QtCore, QtGui

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
        splitter.addWidget(self.CfxEditor)
        splitter.addWidget(middle)
        splitter.addWidget(self.properties)

        hbox.addWidget(splitter)
        self.setLayout(hbox)
        # noinspection PyTypeChecker
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))

        self.setGeometry(300, 300, 300, 200)
        #self.setWindowTitle('QtGui.QSplitter')
        #self.show()

    def onChanged(self, text):
        self.lbl.setText(text)
        self.lbl.adjustSize()

class window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.main = main()

        exitAction = QtGui.QAction("&Exit", self)
        exitAction.triggered.connect(self.close)

        resetAction = QtGui.QAction("&Reset", self)
        resetAction.triggered.connect(self.main.CfxEditor.resetGraph)

        self.lastsaved = {}
        saveAction = QtGui.QAction("&Save", self)

        def savedmove(self, func):
            self.lastsaved = func()
            print(self.lastsaved)

        saveAction.triggered.connect(lambda: savedmove(self, self.main.CfxEditor.save))

        loadAction = QtGui.QAction("&Load last", self)
        loadAction.triggered.connect(lambda: self.main.CfxEditor.load(self.lastsaved))

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(exitAction)
        fileMenu.addAction(resetAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(loadAction)

        self.setCentralWidget(self.main)

        self.show()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    widget = window()
    #widget = main()
    widget.show()

    sys.exit(app.exec_())
