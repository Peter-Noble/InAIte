import sys
import math
from PySide import QtCore, QtGui


class Curve(QtGui.QGraphicsItem):
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

    def check(self):
        if not self.scene() or self.scene().mouseGrabberItem() is self:
            self.newPos = self.pos()
            return
        sceneRect = self.scene().sceneRect()
        self.newPos = self.pos()

    def advance(self):
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
        self.graph.itemMoved()
        return QtGui.QGraphicsItem.itemChange(self, change, value)

    def mouseMoveEvent(self, event):
        QtGui.QGraphicsItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
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
    graphChanged = QtCore.Signal()

    def __init__(self):
        QtGui.QGraphicsView.__init__(self)

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
        self.setMinimumHeight(110)
        self.nodes = []
        self.curves = []
        self.checkcorners()
        # self.setMinimumSize(400, 100)
        noscroll = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        self.setHorizontalScrollBarPolicy(noscroll)
        self.setVerticalScrollBarPolicy(noscroll)

    def itemMoved(self):
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

    def checkcorners(self):
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
        for curve in self.curves:
            self.scene.removeItem(curve)
        self.curves = []
        sor = sorted(self.nodes, key=lambda node: node.pos().x())
        for node in range(len(sor)-1):
            c = Curve(sor[node].pos(), sor[node+1].pos())
            self.scene.addItem(c)
            self.curves.append(c)

        sigout = ("linear",
                  [(node.pos().x(), node.pos().y()) for node in self.nodes])
        # TODO  "linear" needs to be replaced once there are curves
        self.graphChanged.emit()
        # TODO  This needs to broadcast the data that is going to be saved

    def setGraph(self, data):
        pass


class GraphEditor(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        vbox = QtGui.QVBoxLayout()
        self.gw = GraphWidget()
        vbox.addWidget(self.gw)
        vbox.setGeometry(QtCore.QRect(-220, -60, 4400, 120))

        self.setLayout(vbox)
        self.setMinimumSize(450, 140)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #self.setMinimumSize(800, 500)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    QtCore.qsrand(QtCore.QTime(0, 0, 0).secsTo(QtCore.QTime.currentTime()))

    widget = cfx_editor()
    widget.show()

    sys.exit(app.exec_())
