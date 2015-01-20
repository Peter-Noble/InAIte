import sys
import math
from PySide import QtCore, QtGui
import collections
from copy import deepcopy
from cfx_nodeFunctions import logictypes, animationtypes


class Edge(QtGui.QGraphicsItem):
    """The GUI representation of connections between nodes drawn as arrows"""
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QtGui.QGraphicsItem.UserType + 2

    def __init__(self, sourceNode, destNode):
        QtGui.QGraphicsItem.__init__(self)

        self.arrowSize = 10.0
        self.sourcePoint = QtCore.QPointF()
        self.destPoint = QtCore.QPointF()
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.source = sourceNode
        self.dest = destNode
        self.source.addEdge(self)
        self.dest.addEdge(self)
        self.adjust()

    def type(self):
        return Edge.Type

    def sourceNode(self):
        return self.source

    def setSourceNode(self, node):
        self.source = node
        self.adjust()

    def destNode(self):
        return self.dest

    def setDestNode(self, node):
        self.dest = node
        self.adjust()

    def adjust(self):
        """Recalculate the position of the arrow"""
        if not self.source or not self.dest:
            return

        line = QtCore.QLineF(self.mapFromItem(self.source, 0, 0),
                             self.mapFromItem(self.dest, 0, 0))
        length = line.length()

        if length == 0.0:
            return

        # source and dest are the wrong way round.
        # Source is the one being pointed at. Dest is the one pointing from.

        sourceOffsetx = (line.dx() * math.sqrt(self.source.width**2 +
                                               self.source.height**2)) / length
        if sourceOffsetx > self.source.width:
            sourceOffsetx = self.source.width
        elif sourceOffsetx < -self.source.width:
            sourceOffsetx = -self.source.width
        sourceOffsety = (line.dy() * math.sqrt(self.source.width**2 +
                                               self.source.height**2)) / length
        if sourceOffsety > self.source.height:
            sourceOffsety = self.source.height
        elif sourceOffsety < -self.source.height:
            sourceOffsety = -self.source.height

        sourceEdgeOffset = QtCore.QPointF(sourceOffsetx, sourceOffsety)
        # edgeOffset = QtCore.QPointF((line.dx() * 10) / length, (line.dy() *
        # 10) / length)

        destOffsetx = (line.dx() * math.sqrt(self.dest.width**2 +
                                             self.dest.height**2)) / length
        if destOffsetx > self.dest.width:
            destOffsetx = self.dest.width
        elif destOffsetx < -self.dest.width:
            destOffsetx = -self.dest.width
        destOffsety = (line.dy() * math.sqrt(self.dest.width**2 +
                                             self.dest.height**2)) / length
        if destOffsety > self.dest.height:
            destOffsety = self.dest.height
        elif destOffsety < -self.dest.height:
            destOffsety = -self.dest.height

        destEdgeOffset = QtCore.QPointF(destOffsetx, destOffsety)

        self.prepareGeometryChange()
        self.sourcePoint = line.p1() + sourceEdgeOffset
        self.destPoint = line.p2() - destEdgeOffset
        # self.sourcePoint = line.p1()
        # self.destPoint = line.p2()

    def boundingRect(self):
        if not self.source or not self.dest:
            return QtCore.QRectF()

        penWidth = 1
        extra = (penWidth + self.arrowSize) / 2.0

        sizef = QtCore.QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                              self.destPoint.y() -
                              self.sourcePoint.y())
        retqrectf = QtCore.QRectF(self.sourcePoint, sizef)
        retqrectf = retqrectf.normalized().adjusted(-extra, -extra,
                                                    extra, extra)
        return retqrectf

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        # Draw the line itself.
        line = QtCore.QLineF(self.sourcePoint, self.destPoint)

        if line.length() == 0.0:
            return

        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine,
                                  QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = Edge.TwoPi - angle

        qpf1 = QtCore.QPointF(math.sin(angle + Edge.Pi / 3) * self.arrowSize,
                              math.cos(angle + Edge.Pi / 3) * self.arrowSize)
        sourceArrowP1 = self.sourcePoint + qpf1

        angpi = angle + Edge.Pi - Edge.Pi / 3
        qpf2 = QtCore.QPointF(math.sin(angpi) * self.arrowSize,
                              math.cos(angpi) * self.arrowSize)
        sourceArrowP2 = self.sourcePoint + qpf2

        painter.setBrush(QtCore.Qt.black)
        painter.drawPolygon(QtGui.QPolygonF([line.p1(), sourceArrowP1,
                                             sourceArrowP2]))


class Node(QtGui.QGraphicsItem):
    """The GUI representation of nodes drawn as coloured box.
    Contains settings used for properties"""
    Type = QtGui.QGraphicsItem.UserType + 1
    ZValue = -1
    isFrame = False

    def __init__(self, graphWidget):
        QtGui.QGraphicsItem.__init__(self)

        self.UpdateSelected = graphWidget.UpdateSelected

        self.UID = graphWidget.getUID()

        self.graph = graphWidget
        self.edgeList = []
        self.newPos = QtCore.QPointF()
        self.relFramePos = QtCore.QPointF()
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(self.DeviceCoordinateCache)
        self.setZValue(self.ZValue)  # Decides the stacking order

        self.selected = False
        self.frameparent = None
        self.group = self.graph.nodes

        self.width = 64  # actual width = 2*self.width = 128
        self.height = 32  # actual height = 2*self.height = 64

        self.colour = QtCore.Qt.darkGreen

        self.settings = collections.OrderedDict()

        self.displayname = "Node"

    def addEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList

    def advance(self):
        if self.newPos == self.pos():
            return False

        # self.setPos(self.newPos)
        return True

    def boundingRect(self):
        """sets the area that is updated by drawing"""
        adjust = 4.0
        return QtCore.QRectF(-self.width - adjust, -self.height - adjust,
                             2 * self.width + 2 * adjust, 2 * self.height +
                             2 * adjust)

    def shape(self):
        """The area that can be clicked in"""
        path = QtGui.QPainterPath()
        adjust = 2
        path.addRect(-self.width - adjust, -self.height - adjust,
                     2 * self.width + 2 * adjust, 2 * self.height + 2 * adjust)
        return path

    def paint(self, painter, option, widget):
        painter.setPen(QtCore.Qt.NoPen)
        if option.state & QtGui.QStyle.State_Sunken:
            painter.setPen(QtGui.QPen(QtCore.Qt.yellow, 4))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.darkGray, 4))
        if self.selected:
            painter.setPen(QtGui.QPen(painter.pen().color().darker(), 4))

        painter.setBrush(QtGui.QBrush(self.colour))
        backgroundRect = QtCore.QRect(-self.width, -self.height,
                                      2 * self.width, 2 * self.height)
        painter.drawRect(backgroundRect)

        # TODO set the colour of text so that it is actually readable against
        # the colour of the node
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        text = QtGui.QFont("Arial", 8, QtGui.QFont.Bold)
        painter.setFont(text)
        painter.drawText(backgroundRect, QtCore.Qt.AlignCenter,
                         self.displayname)

    def itemChange(self, change, value):
        # TODO please think about what this funcion is doing... twice
        for edge in self.edgeList:
            edge.adjust()
        if change == QtGui.QGraphicsItem.ItemPositionChange:
            for edge in self.edgeList:
                edge.adjust()
            self.graph.itemMoved()

        return QtGui.QGraphicsItem.itemChange(self, change, value)

    def isInFrame(self):
        """Called when a node is dropped.
        Deals with adding the node to a frame"""
        inany = False
        prevparent = self.frameparent
        # is the node within the area of a frame
        for frame in self.graph.nodes:
            if frame.isFrame and (self != frame):
                minx = frame.pos().x() - frame.width + self.width
                hphmb = frame.height + self.height - frame.barheight
                miny = frame.pos().y() - hphmb
                maxx = frame.pos().x() + frame.width - self.width
                maxy = frame.pos().y() + frame.height - self.height
                if (self.pos().x() >= minx) and (self.pos().x() <= maxx):
                    if (self.pos().y() >= miny) and (self.pos().y() <= maxy):
                        inany = True
                        self.frameparent = frame
        # TODO sort out all these Nones
        # moved into frame from no frame
        if (prevparent is None) and (self.frameparent is not None):
            self.frameparent.addChild(self)
        # If moved outside frame
        if not inany:
            if prevparent:
                for child in prevparent.children:
                    if child[0] == self:
                        prevparent.children.remove(child)
                    self.frameparent = None
        # If moved within same frame
        if (prevparent is not None) and (self.frameparent is not None):
            if (prevparent.UID == self.frameparent.UID):
                fpc = self.frameparent.children
                for child in range(len(fpc)):
                    if fpc[child][0] == self:
                        fpc[child] = (fpc[child][0],
                                      self.pos() - self.frameparent.pos())
        # Moved to new frame
            elif (not (prevparent.UID == self.frameparent.UID)):
                for child in prevparent.children:
                    if child[0] == self:
                        prevparent.children.remove(child)
                        self.frameparent.addChild(self)

    def mousePressEvent(self, event):
        self.update()
        QtGui.QGraphicsItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.update()
        QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
        sel = True
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            for node in self.group:
                if node.selected and node != self:
                    self.graph.addEdge(node, self)
                    node.selected = False
                    node.update()
                    sel = False
            if sel:
                self.selected = not self.selected
            self.UpdateSelected(self if self.selected else None)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.isInFrame()


class LogicNode(Node):
    """Nodes that control behavour"""
    def __init__(self, graphWidget):
        self.category = ("AND", [x for x in logictypes])
        Node.__init__(self, graphWidget)


class MotionNode(Node):
    """Nodes that represent an animation"""
    def __init__(self, graphWidget):
        Node.__init__(self, graphWidget)
        self.colour = QtCore.Qt.blue
        self.category = ("STD", [x for x in animationtypes])


class MotionFrame(MotionNode):
    """Node that represents an animation and contains logic nodes that are
    only evaluated if animation is playing"""
    def __init__(self, graphWidget):
        self.children = []
        MotionNode.__init__(self, graphWidget)
        self.colour = QtCore.Qt.darkCyan

        self.width = 64*4
        self.height = 32*4
        self.barheight = 24
        self.isFrame = True
        self.setZValue(-2)

    def paint(self, painter, option, widget):
        painter.setPen(QtCore.Qt.NoPen)
        if option.state & QtGui.QStyle.State_Sunken:
            painter.setPen(QtGui.QPen(QtCore.Qt.yellow, 4))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.darkGray, 4))
        if self.selected:
            painter.setPen(QtGui.QPen(painter.pen().color().darker(), 4))

        painter.setBrush(QtGui.QBrush(self.colour))
        painter.drawRect(-self.width, -self.height,
                         2 * self.width, 2 * self.height)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        painter.drawRect(-self.width, -(self.height - self.barheight),
                         2 * self.width, -self.barheight)

        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        text = QtGui.QFont("Arial", 8, QtGui.QFont.Bold)
        painter.setFont(text)
        painter.drawText(QtCore.QRect(-self.width,
                                      -(self.height - self.barheight),
                                      2 * self.width, -self.barheight),
                         QtCore.Qt.AlignCenter, self.displayname)

    def addChild(self, child):
        self.children.append([child, child.pos() - self.pos()])

    def itemChange(self, change, value):
        """move the frame's children with it"""
        MotionNode.itemChange(self, change, value)
        for child in self.children:
            diff = self.pos() + child[1]
            child[0].setPos(diff)
        self.graph.itemMoved()
        return QtGui.QGraphicsItem.itemChange(self, change, value)

NODETYPES = [
    # (NAME STRING ,NODECLASS),
    ("LogicNode", LogicNode),
    ("MotionNode", MotionNode),
    ("MotionFrame", MotionFrame)
]
# TODO replace this with a collections.OrderedDict()


class CfxEditor(QtGui.QGraphicsView):
    """The window in which the nodes and edges live"""
    nodes = []
    edges = []

    def __init__(self, UpdateSelected):
        QtGui.QGraphicsView.__init__(self)

        self.UpdateSelected = UpdateSelected

        self.timerId = 0

        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setSceneRect(-200, -200, 400, 400)
        self.setScene(self.scene)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)

        self.setBackgroundBrush(QtCore.Qt.lightGray)
        # self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)

        self.scale(0.8, 0.8)
        self.setMinimumSize(800, 500)
        self.setWindowTitle(self.tr("cfx_editor"))

    def getUID(self):
        UID = 0
        current = []
        for node in self.nodes:
            current.append(node.UID)
        while True:
            if UID in current:
                UID += 1
            else:
                return UID

    def addNode(self, nodeType):
        item = nodeType(self)
        self.nodes.append(item)
        self.scene.addItem(item)

    def itemMoved(self):
        if not self.timerId:
            self.timerId = self.startTimer(1000 / 25)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            cont = True
            node = 0
            while (node < len(self.nodes)) and cont:
                if self.nodes[node].selected:
                    edge = len(self.edges)-1
                    while edge >= 0:
                        if self.edges[edge] in self.nodes[node].edges():
                            self.scene.removeItem(self.edges[edge])
                            del self.edges[edge]
                        edge -= 1
                    self.scene.removeItem(self.nodes[node])
                    del self.nodes[node]
                    cont = False
                node += 1
        else:
            QtGui.QGraphicsView.keyPressEvent(self, event)

    def timerEvent(self, event):
        for node in self.nodes:
            node.advance()

        itemsmoved = False
        for node in self.nodes:
            if node.advance():
                itemsmoved = True

        if not itemsmoved:
            self.killTimer(self.timerId)
            self.timerId = 0

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, +event.delta() / 240.0))

    def scaleView(self, scaleFactor):
        # TODO this function needs sorting out. Zooming is weird at the moment
        factor = self.matrix().scale(scaleFactor, scaleFactor)
        factor = factor.mapRect(QtCore.QRectF(0, 0, 1, 1)).width()

        if factor < 0.5 or factor > 10:
            return

        self.scale(scaleFactor, scaleFactor)

    def addEdge(self, fromNode, toNode):
        """decided which requests for new edges should be allowed"""
        if issubclass(fromNode.__class__, LogicNode):
            if issubclass(toNode.__class__, MotionNode):
                return None
            for e in self.edges:
                con = [e.source, e.dest]
                if fromNode in con and toNode in con:
                    return None
        elif issubclass(fromNode.__class__, MotionNode):
            if issubclass(toNode.__class__, LogicNode):
                return None
            for e in self.edges:
                if (fromNode == e.dest) and (toNode == e.source):
                    return None
        ed = Edge(toNode, fromNode)
        self.edges.append(ed)
        self.scene.addItem(ed)

    def resetGraph(self):
        for item in self.nodes+self.edges:
            self.scene.removeItem(item)
        self.nodes = []
        self.edges = []

    def save(self):
        """Turn the node graph into a string"""
        tosave = {"nodes": {}, "edges": []}
        typest = ""
        for node in self.nodes:
            for types in NODETYPES:
                if types[1] == node.__class__:
                    typest = types[0]
            settings = deepcopy(node.settings)
            for s in settings:
                if isinstance(settings[s], str):
                    settings[s] = settings[s].replace("\n", "{NEWLINE}")
            fp = node.frameparent.UID if node.frameparent else None,
            tosave["nodes"][node.UID] = {
                "UID": node.UID,
                "type": typest,
                "posx": node.pos().x(),
                "posy": node.pos().y(),
                "frameparent": fp,
                "settings": node.settings,
                "category": node.category,
                "displayname": node.displayname
            }
        for edge in self.edges:
            tosave["edges"].append({
                "source": edge.source.UID,
                "dest": edge.dest.UID
            })
        return tosave

    def load(self, toload):
        self.resetGraph()
        toparent = []
        for node in toload["nodes"]:
            lono = toload["nodes"][node]  # lono = alias for current node
            item = [x[1] for x in NODETYPES if x[0] == lono["type"]][0](self)
            item.colour = logictypes[lono["category"][0]].colour
            item.UID = lono["UID"]
            item.setPos(lono["posx"], lono["posy"])
            item.settings = lono["settings"]
            itse = item.settings
            item.displayname = lono["displayname"]
            for s in itse:
                if isinstance(itse[s], str):
                    itse[s] = itse[s].replace("{NEWLINE}", "\n")
            item.category = lono["category"]
            if lono["frameparent"]:
                toparent.append((item, lono["frameparent"]))
            self.nodes.append(item)
            self.scene.addItem(item)

        for parent in toparent:
            frame = [x for x in self.nodes if x.UID == parent[1]]
            if len(frame) > 0:
                frame[0].addChild(parent[0])
                parent[0].frameparent = frame[0]

        for edge in toload["edges"]:
            self.addEdge([x for x in self.nodes if x.UID == edge["dest"]][0],
                         [x for x in self.nodes if x.UID == edge["source"]][0])


# If this file isn't being imported do the following...
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    widget = CfxEditor(lambda x: print("Not connected"))
    widget.show()

    sys.exit(app.exec_())
