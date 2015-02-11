import sys
import math
from PySide import QtCore, QtGui
import collections
import functools
import copy
from cfx_nodeFunctions import logictypes, statetypes

# from cfx_graphWidget import GraphEditor
import imp
import cfx_graphWidget
imp.reload(cfx_graphWidget)
GraphEditor = cfx_graphWidget.GraphEditor


class Properties(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.propbox = QtGui.QVBoxLayout()
        self.setLayout(self.propbox)

        self.setMinimumSize(800, 200)

    def updateProp(self, selected, key, val):
        selected.settings[key] = val
        selected.update()

    def updateBoolProp(self, selected, key, val):
        selected.settings[key] = True if val == 2 else False
        selected.update()

    def updateGraphProp(self, selected, key, val):
        store = [(node.pos().x(), node.pos().y()) for node in val.gw.nodes]
        results = (selected.settings[key]["value"][0], store)
        selected.settings[key]["value"] = results
        selected.update()

    def updatetextedit(self, selected, key, textedit):
        selected.settings[key]["value"] = textedit.toPlainText()
        selected.update()

    def updateDisplayName(self, selected, name):
        selected.displayname = name
        selected.update()

    def updateType(self, selected, item, totype):
        nametotype = item.itemText(totype)
        if nametotype in logictypes:
            selected.colour = logictypes[nametotype].colour
            selected.settings = copy.deepcopy(logictypes[nametotype].settings)
        elif nametotype in statetypes:
            selected.colour = statetypes[nametotype].colour
            selected.settings = copy.deepcopy(statetypes[nametotype].settings)
        selected.category = (nametotype, selected.category[1])
        self.newSelected(selected)
        selected.update()

    def updateTuple(self, selected, key, totype):
        selected.settings[key] = (selected.settings[key][1][totype],
                                  selected.settings[key][1])
        selected.update()

    def newSelected(self, selected):
        self.clearLayout(self.propbox)
        if selected:
            height = 0
            width = 0
            row = QtGui.QHBoxLayout()
            lbl1 = QtGui.QLabel("Display Name")
            height += lbl1.minimumHeight()
            width = max(width, lbl1.minimumWidth())
            row.addWidget(lbl1)

            item = QtGui.QLineEdit()
            item.setText(selected.displayname)
            item.textChanged.connect(functools.partial(self.updateDisplayName,
                                                       selected))
            height += item.minimumHeight()
            width = max(width, item.minimumWidth())
            row.addWidget(item)
            self.propbox.addLayout(row)

            row = QtGui.QHBoxLayout()
            lbl2 = QtGui.QLabel("Category")
            height += lbl2.minimumHeight()
            width = max(width, lbl2.minimumWidth())
            row.addWidget(lbl2)

            item = QtGui.QComboBox()
            item.addItems(selected.category[1])
            item.setCurrentIndex(item.findText(selected.category[0]))
            item.currentIndexChanged.connect(functools.partial(self.updateType,
                                             selected, item))
            height += item.minimumHeight()
            width = max(width, item.minimumWidth())
            row.addWidget(item)
            self.propbox.addLayout(row)

            partial = functools.partial

            for prop in selected.settings:
                val = selected.settings[prop]
                row = QtGui.QHBoxLayout()
                row.addWidget(QtGui.QLabel(prop))
                if isinstance(val, bool):
                    item = QtGui.QCheckBox()
                    item.setCheckState(QtCore.Qt.CheckState(val*2))
                    item.stateChanged.connect(partial(self.updateBoolProp,
                                                      selected, prop))
                    row.addWidget(item)
                elif isinstance(val, int):
                    item = QtGui.QSpinBox()
                    item.setRange(-99999, 99999)
                    item.setValue(val)
                    item.valueChanged.connect(partial(self.updateProp,
                                              selected, prop))
                    row.addWidget(item)
                elif isinstance(val, float):
                    item = QtGui.QDoubleSpinBox()
                    item.setRange(-99999, 99999)
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
                elif isinstance(val, dict):
                    """This is for special data types"""
                    if val["type"] == "MLEdit":
                        item = QtGui.QTextEdit()
                        item.setText(val["value"])
                        item.textChanged.connect(partial(self.updatetextedit,
                                                         selected, prop, item))
                        row.addWidget(item)
                    if val["type"] == "Graph":
                        item = GraphEditor()
                        item.gw.setGraph(val["value"])
                        item.gw.graphChanged.connect(partial(
                                                     self.updateGraphProp,
                                                     selected, prop, item)
                                                     )
                        row.addWidget(item)
                height += item.minimumHeight()
                width = max(width, item.minimumWidth())
                self.propbox.addLayout(row)
            self.propbox.addStretch()
            self.setMinimumSize(width, height)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clearLayout(child.layout())
