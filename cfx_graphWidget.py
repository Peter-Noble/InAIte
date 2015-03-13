import sys
import math
from PySide import QtCore, QtGui


class Curve(QtGui.QGraphicsItem):
    """The lines that connect the points on the graph"""
    def __init__(self, gofrom, goto):
        QtGui.QGraphicsItem.__init__(self)
        self.goto = goto
        self.gofrom = gofrom

    def paint(self, painter, option, widget):
        if self.goto:
            path = QtGui.QPainterPath()
            path.moveTo(self.gofrom)
            difference = self.gofrom.x() - self.goto.x()
            # c1 = self.gofrom
            # c1.setX(c1.x() - (difference/3))
            # c2 = self.goto
            # c2.setX(c2.x() + (difference/3))
            # path.cubicTo(self.gofrom, self.goto, self.goto)
            path.lineTo(self.goto)
            painter.drawPath(path)
            self.goingto = self.goto

    def boundingRect(self):
        if not self.gofrom or not self.goto:
            return QtCore.QRectF()

        penWidth = 1
        extra = 4
        size = QtCore.QSizeF(self.goto.x() - self.gofrom.x(),
                             self.goto.y() - self.gofrom.y())

        rect = QtCore.QRectF(self.gofrom, size)

        return rect.normalized().adjusted(-extra, -extra, extra, extra)


class Node(QtGui.QGraphicsItem):
    """The points on the graph"""
    Type = QtGui.QGraphicsItem.UserType + 1

    def __init__(self, graphWidget):
        QtGui.QGraphicsItem.__init__(self)

        self.graph = graphWidget
        self.newPos = QtCore.QPointF()
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(self.DeviceCoordinateCache)
        self.setZValue(-1)

        self.goingto = self.pos()

    def showToolTip(self):
        """Display coordinates (as the simulation will us them) in tooltip"""
        x = (self.scenePos().x() - 200) / 200
        y = (self.scenePos().y() - 100) / 100
        if self.toolTip() != "{0}, {1}".format(x, y):
            self.setToolTip("{0}, {1}".format(x, y))

    def check(self):
        if not self.scene() or self.scene().mouseGrabberItem() is self:
            self.newPos = self.pos()
            return
        sceneRect = self.scene().sceneRect()
        self.newPos = self.pos()

    def advance(self):
        """Node changed"""
        if self.newPos == self.pos():
            return False

        self.setPos(self.newPos)
        return True

    def boundingRect(self):
        """sets the area that is updated by drawing"""
        adjust = 4.0
        return QtCore.QRectF(-3 - adjust, -3 - adjust,
                             6 + 2 * adjust, 6 + 2 * adjust)

    def paint(self, painter, option, widget):
        painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
        painter.drawEllipse(-3, -3, 6, 6)

    def itemChange(self, change, value):
        """Position of the node changed"""
        self.graph.itemMoved()
        return QtGui.QGraphicsItem.itemChange(self, change, value)

    def mouseMoveEvent(self, event):
        """When the position of the node changed"""
        self.showToolTip()
        QtGui.QGraphicsItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """Node dropped"""
        sceneRect = self.scene().sceneRect()
        tmp = self.pos()
        if self.pos().x() < sceneRect.left():
            tmp.setX(sceneRect.left())
        elif self.pos().x() > sceneRect.right():
            tmp.setX(sceneRect.right())
        if self.pos().y() > sceneRect.bottom():
            tmp.setY(sceneRect.bottom())
        elif self.pos().y() < sceneRect.top():
            tmp.setY(sceneRect.top())
        self.setPos(tmp)
        QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
        self.graph.checkcorners()


class GraphWidget(QtGui.QGraphicsView):
    """For editing graphs as a property of a node"""
    graphChanged = QtCore.Signal()

    def __init__(self):
        QtGui.QGraphicsView.__init__(self)

        # TODO  add x=0 line and/or background grid

        self.timerId = 0
        self.scene = QtGui.QGraphicsScene()
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setSceneRect(0, 0, 400, 100)
        self.setScene(self.scene)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setBackgroundBrush(QtCore.Qt.lightGray)
        self.setMinimumSize(410, 110)
        self.setMaximumSize(410, 110)
        # self.setMinimumHeight(110)
        self.nodes = []
        self.curves = []
        self.checkcorners()
        # self.setMinimumSize(400, 100)
        noscroll = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        self.setHorizontalScrollBarPolicy(noscroll)
        self.setVerticalScrollBarPolicy(noscroll)

    def itemMoved(self):
        "Node has been dragged"
        if not self.timerId:
            self.timerId = self.startTimer(1000 / 25)

    def timerEvent(self, event):
        for node in self.nodes:
            node.check()

        itemsMoved = False
        for node in self.nodes:
            if node.advance():
                itemsMoved = True

        if not itemsMoved:
            self.killTimer(self.timerId)
            self.timerId = 0

    def addCurves(self):
        """Connect nodes"""
        for curve in self.curves:
            self.scene.removeItem(curve)

        tmp = {}
        for r in self.nodes:
            if r.pos().x() in tmp:
                tmp[r.pos().x()] = min(tmp[r.pos().x()], r.pos().y())
            else:
                tmp[r.pos().x()] = r.pos().y()
        sor = sorted(tmp.items(), key=lambda x: x[0])

        for node in range(len(sor)-1):
            fro = QtCore.QPoint(sor[node][0], sor[node][1])
            to = QtCore.QPoint(sor[node+1][0], sor[node+1][1])
            c = Curve(fro, to)
            self.scene.addItem(c)
            self.curves.append(c)

    def checkcorners(self):
        """If the nodes in the corner have been moved then create new ones"""
        putleft = True
        foundleft = False
        putright = True
        foundright = False
        sr = self.scene.sceneRect()
        totrash = []
        for node in self.nodes:
            if node.pos().x() == 0 and node.pos().y() == sr.bottom():
                putleft = False
                if foundleft:
                    totrash.append(node)
                    self.scene.removeItem(node)
                else:
                    foundleft = True
            if node.pos().x() == sr.right() and node.pos().y() == sr.bottom():
                putright = False
                if foundright:
                    totrash.append(node)
                    self.scene.removeItem(node)
                else:
                    foundright = True
        for node in totrash:
            self.nodes.remove(node)
        if putleft:
            item = Node(self)
            item.setPos(0, sr.bottom())
            self.nodes.append(item)
            self.scene.addItem(item)
        if putright:
            item = Node(self)
            item.setPos(sr.right(), sr.bottom())
            self.nodes.append(item)
            self.scene.addItem(item)
        self.addCurves()
        self.graphChanged.emit()

    def setGraph(self, data):
        """Load the graph from the data in a node"""
        for node in data[1]:
            item = Node(self)
            item.setPos(node[0], node[1])
            x = (node[0] - 200) / 200
            y = (node[1] - 100) / 100
            item.setToolTip("{0}, {1}".format(x, y))
            self.nodes.append(item)
            self.scene.addItem(item)
        self.addCurves()


class GraphEditor(QtGui.QWidget):
    """Contains the graph viewer so it can be added to properties editor"""
    def __init__(self):
        QtGui.QWidget.__init__(self)

        vbox = QtGui.QVBoxLayout()
        self.gw = GraphWidget()
        vbox.addWidget(self.gw)
        self.setLayout(vbox)


if __name__ == "__main__":
    """For testing purposes"""
    app = QtGui.QApplication(sys.argv)
    QtCore.qsrand(QtCore.QTime(0, 0, 0).secsTo(QtCore.QTime.currentTime()))

    vbox = QtGui.QVBoxLayout()
    row = QtGui.QHBoxLayout()
    row.addWidget(QtGui.QLabel("Hello"))
    row.addWidget(QtGui.QSpinBox())
    vbox.addLayout(row)
    row = QtGui.QHBoxLayout()
    widget = GraphEditor()
    row.addWidget(QtGui.QLabel("Hello"))
    row.addWidget(widget)
    vbox.addLayout(row)
    window = QtGui.QWidget()
    row = QtGui.QHBoxLayout()
    row.addWidget(QtGui.QLabel("Hello"))
    row.addWidget(QtGui.QLabel("Hello"))
    vbox.addLayout(row)

    window.setLayout(vbox)
    window.show()

    sys.exit(app.exec_())
