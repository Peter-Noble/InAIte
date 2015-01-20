import sys
import math
from PySide import QtCore, QtGui
import collections
import functools
import copy
from cfx_nodeFunctions import logictypes, animationtypes


class GraphWidget(QtGui.QWidget):
    # TODO make this work!!!
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setMinimumSize(1, 30)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        font = QtGui.QFont('Serif', 7, QtGui.QFont.Light)
        qp.setFont(font)

        size = self.size()
        w = size.width()
        h = size.height()

        till = int(((w / 750.0) * self.value))
        full = int(((w / 750.0) * 700))

        if self.value >= 700:
            qp.setPen(QtGui.QColor(255, 255, 255))
            qp.setBrush(QtGui.QColor(255, 255, 184))
            qp.drawRect(0, 0, full, h)
            qp.setPen(QtGui.QColor(255, 175, 175))
            qp.setBrush(QtGui.QColor(255, 175, 175))
            qp.drawRect(full, 0, till-full, h)
        else:
            qp.setPen(QtGui.QColor(255, 255, 255))
            qp.setBrush(QtGui.QColor(255, 255, 184))
            qp.drawRect(0, 0, till, h)

        pen = QtGui.QPen(QtGui.QColor(20, 20, 20), 1,
                         QtCore.Qt.SolidLine)

        qp.setPen(pen)
        qp.setBrush(QtCore.Qt.NoBrush)
        qp.drawRect(0, 0, w-1, h-1)
        qp.end()


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

        self.setMinimumSize(800, 200)

    def updateProp(self, selected, key, val):
        selected.settings[key] = val
        selected.update()

    def updatetextedit(self, selected, key, textedit):
        selected.settings[key]["value"] = textedit.toPlainText()
        selected.update()

    def updateDisplayName(self, selected, name):
        selected.displayname = name
        selected.update()

    def updateType(self, selected, item, totype):
        nametotype = item.itemText(totype)
        selected.colour = logictypes[nametotype].colour
        selected.category = (nametotype, selected.category[1])
        selected.settings = copy.deepcopy(logictypes[nametotype].settings)
        self.newSelected(selected)
        selected.update()

    def updateTuple(self, selected, key, totype):
        selected.settings[key] = (selected.settings[key][1][totype],
                                  selected.settings[key][1])
        selected.update()

    def newSelected(self, selected):
        self.clearLayout(self.propbox)
        if selected:

            row = QtGui.QHBoxLayout()
            row.addWidget(QtGui.QLabel("Display Name"))
            item = QtGui.QLineEdit()
            item.setText(selected.displayname)
            item.textChanged.connect(functools.partial(self.updateDisplayName,
                                                       selected))
            row.addWidget(item)
            self.propbox.addLayout(row)

            row = QtGui.QHBoxLayout()
            row.addWidget(QtGui.QLabel("Category"))
            item = QtGui.QComboBox()
            item.addItems(selected.category[1])
            item.setCurrentIndex(item.findText(selected.category[0]))
            item.currentIndexChanged.connect(functools.partial(self.updateType,
                                             selected, item))
            row.addWidget(item)
            self.propbox.addLayout(row)

            partial = functools.partial

            for prop in selected.settings:
                val = selected.settings[prop]
                row = QtGui.QHBoxLayout()
                row.addWidget(QtGui.QLabel(prop))
                if isinstance(val, int):
                    item = QtGui.QSpinBox()
                    item.setValue(val)
                    item.valueChanged.connect(partial(self.updateProp,
                                              selected, prop))
                    row.addWidget(item)
                elif isinstance(val, float):
                    item = QtGui.QDoubleSpinBox()
                    item.setValue(val)
                    item.valueChanged.connect(partial(self.updateProp,
                                              selected, prop))
                    row.addWidget(item)
                elif isinstance(val, str):
                    item = QtGui.QLineEdit()
                    item.setText(val)
                    item.textChanged.connect(partial(self.updateProp,
                                                     selected, prop))
                    row.addWidget(item)
                elif isinstance(val, tuple):
                    item = QtGui.QComboBox()
                    item.addItems(val[1])
                    item.setCurrentIndex(item.findText(val[0]))
                    item.currentIndexChanged.connect(partial(self.updateTuple,
                                                             selected, prop))
                    row.addWidget(item)
                elif isinstance(val, bool):
                    item = QtGui.QCheckBox()
                    item.setCheckState(val)
                    item.stateChanged.connect(partial(self.updateProp,
                                                      selected, prop))
                    row.addWidget(item)
                elif isinstance(val, dict):
                    """This is for special data types"""
                    if val["type"] == "MLEdit":
                        item = QtGui.QTextEdit()
                        item.setText(val["value"])
                        item.textChanged.connect(partial(self.updatetextedit,
                                                         selected, prop, item))
                        row.addWidget(item)
                self.propbox.addLayout(row)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clearLayout(child.layout())
