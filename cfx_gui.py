import sys
import math
from PySide import QtCore, QtGui

from cfx_nodeEditor import CfxEditor, NODETYPES


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


class Properties(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.lbl = QtGui.QLabel()
        self.lbl.setText("This is where the properties will go")
        self.box = QtGui.QHBoxLayout()
        self.box.addWidget(self.lbl)
        self.setLayout(self.box)


class main(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        hbox = QtGui.QHBoxLayout(self)

        top = CfxEditor()
        middle = NodeList(top)
        bottom = Properties()

        splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(top)
        splitter.addWidget(middle)
        splitter.addWidget(bottom)

        hbox.addWidget(splitter)
        self.setLayout(hbox)
        # noinspection PyTypeChecker
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('QtGui.QSplitter')
        self.show()

    def onChanged(self, text):
        self.lbl.setText(text)
        self.lbl.adjustSize()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # widget = cfx_editor()
    widget = main()
    widget.show()

    sys.exit(app.exec_())
