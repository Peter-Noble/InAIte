import sys
import math
from PySide import QtCore, QtGui
import collections


class Properties(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.box = QtGui.QVBoxLayout()

        self.lbl = QtGui.QLabel()
        self.lbl.setText("Properties:")
        self.box.addWidget(self.lbl)

        self.box.addSpacing(10)

        self.propbox = QtGui.QVBoxLayout()
        self.box.addLayout(self.propbox)

        self.setLayout(self.box)

    def newSelected(self, selected):
        if selected:
            for prop in selected.settings:
                val = selected.settings[prop]
                row = QtGui.QHBoxLayout()
                row.addWidget(QtGui.QLabel(prop))
                if type(val) == type(int()):
                    print("int")
                    item = QtGui.QSpinBox()
                    item.setValue(val)
                    item.valueChanged.connect(lambda: print("Changes"))
                    row.addWidget(item)
                elif type(val) == type(float()):
                    print("float")
                    item = QtGui.QDoubleSpinBox()
                    item.setValue(val)
                    item.valueChanged.connect(lambda: print("Changes"))
                    row.addWidget(item)
                elif type(selected.settings[prop]) == type(str()):
                    print("string")
                    item = QtGui.QLineEdit()
                    item.setText(val)
                    item.textChanged.connect(lambda: print("changes"))
                    row.addWidget(item)
                self.propbox.addLayout(row)
        else:
            self.clearLayout(self.propbox)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clearLayout(child.layout())

    # TODO editing properties doesn't update the nodes settings.


