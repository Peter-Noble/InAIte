import sys
import math
from PySide import QtCore, QtGui
import collections
from copy import deepcopy
from . import cfx_nodeFunctions
from .cfx_nodeFunctions import logictypes, statetypes

MULTISELECTCOLOUR = QtGui.QColor(255, 204, 0)
HIGHLIGHTCOLOUR = QtCore.Qt.yellow


class Edge(QtGui.QGraphicsItem):
    """The GUI representation of connections between nodes drawn as arrows"""
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QtGui.QGraphicsItem.UserType + 2

    def __init__(self, sourceNode, destNode):
        QtGui.QGraphicsItem.__init__(self)

        self.arrowSize = 10.0
        self.selected = False
        self.multiselected = False
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
        if self.multiselected or self.selected:
            painter.setPen(QtGui.QPen(HIGHLIGHTCOLOUR))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
        if self.multiselected:
            painter.setPen(QtGui.QPen(MULTISELECTCOLOUR, 2))
        if self.selected:
            painter.setPen(QtGui.QPen(painter.pen().color().darker(), 2))
        painter.drawEllipse(line.pointAt(0.5), 4, 4)


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
        self.multiselected = False
        self.frameparent = None
        self.group = self.graph.nodes

        self.width = 64  # actual width = 2*self.width = 128
        self.height = 32  # actual height = 2*self.height = 64

        # self.colour = QtGui.QColor(QtCore.Qt.darkGreen)

        # self.settings = collections.OrderedDict()
        if self.logicormotion == "logic":
            self.settings = deepcopy(logictypes[self.category[0]].settings)
            self.displayname = "Logic"
        else:
            self.settings = deepcopy(statetypes[self.category[0]].settings)
            self.displayname = "Motion"

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
            painter.setPen(QtGui.QPen(HIGHLIGHTCOLOUR, 4))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.darkGray, 4))
        if self.multiselected:
            painter.setPen(QtGui.QPen(MULTISELECTCOLOUR, 4))
        if self.selected:
            painter.setPen(QtGui.QPen(painter.pen().color().darker(), 4))

        painter.setBrush(QtGui.QBrush(self.colour))
        backgroundRect = QtCore.QRect(-self.width, -self.height,
                                      2 * self.width, 2 * self.height)
        painter.drawRect(backgroundRect)

        col = self.colour
        brightness = col.red()*0.299 + col.green()*0.587 + col.blue()*0.114
        if brightness > 105:
            textcol = QtGui.QColor(0, 0, 0)
        else:
            textcol = QtGui.QColor(255, 255, 255)

        painter.setPen(QtGui.QPen(textcol, 1))
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
        self.graph.backgroundClick = False
        self.dragStart = False
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
            Rect = self.graph.scene.itemsBoundingRect()
            Rect.setBottom(max(Rect.bottom(), 200))
            Rect.setTop(min(Rect.top(), -200))
            Rect.setLeft(min(Rect.left(), -200))
            Rect.setRight(max(Rect.right(), 200))
            self.graph.scene.setSceneRect(Rect)

    def mouseMoveEvent(self, event):
        self.dragStart = False
        if not self.dragStart:
            self.dragStart = True
            change = event.scenePos() - event.lastScenePos()
            for node in self.graph.nodes:
                if node != self and (node.selected or node.multiselected):
                    node.setPos(node.pos() + change)
        QtGui.QGraphicsItem.mouseMoveEvent(self, event)


class LogicNode(Node):
    """Nodes that control behavour"""
    def __init__(self, graphWidget):
        self.category = ("INPUT", [x for x in logictypes])
        self.logicormotion = "logic"
        # TODO make the default setting available somewhere better than this
        Node.__init__(self, graphWidget)


class MotionNode(Node):
    """Nodes that represent an animation"""
    def __init__(self, graphWidget):
        # self.colour = QtCore.Qt.blue
        self.category = ("STD", [x for x in statetypes])
        self.logicormotion = "motion"
        Node.__init__(self, graphWidget)


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
            painter.setPen(QtGui.QPen(HIGHLIGHTCOLOUR, 4))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.darkGray, 4))
        if self.multiselected:
            painter.setPen(QtGui.QPen(MULTISELECTCOLOUR, 4))
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
        # self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)

        self.scale(0.8, 0.8)
        self.setMinimumSize(800, 450)
        self.setWindowTitle(self.tr("cfx_editor"))

        self.modifiers = None
        self.viewCenter = QtCore.QPointF(0, 0)

        self.pressedDown = False
        self.backgroundClick = False

        self.rubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)
        self.rubrect = QtCore.QRect(0, 0, 0, 0)
        self.rubMoved = False

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
        cat = item.category[0]
        if cat in logictypes:
            item.colour = logictypes[cat].colour
        elif cat in statetypes:
            item.colour = statetypes[cat].colour
        self.nodes.append(item)
        self.scene.addItem(item)
        for node in self.nodes:
            node.selected = False
            node.multiselected = False
            node.update()
        for edge in self.edges:
            edge.selected = False
            edge.multiselected = False
            edge.update()

    def itemMoved(self):
        if not self.timerId:
            self.timerId = self.startTimer(1000 / 25)

    def keyPressEvent(self, event):
        """Keyboard shortcuts for when in the main editor window"""
        key = event.key()

        self.modifiers = QtGui.QApplication.keyboardModifiers()

        if key == QtCore.Qt.Key_Delete:
            todelnodes = set()
            todeledges = set()
            for m, node in enumerate(self.nodes):
                if node.selected or node.multiselected:
                    for n, edge in enumerate(self.edges):
                        if edge in node.edges():
                            self.scene.removeItem(edge)
                            todeledges.add(n)
                    self.scene.removeItem(node)
                    todelnodes.add(m)
            for n, edge in enumerate(self.edges):
                if edge.selected or edge.multiselected:
                    if n not in todeledges:
                        todeledges.add(n)
                        self.scene.removeItem(edge)
            for edge in sorted(todeledges, reverse=True):
                del self.edges[edge]
            for node in sorted(todelnodes, reverse=True):
                del self.nodes[node]
        else:
            QtGui.QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        self.modifiers = QtGui.QApplication.keyboardModifiers()
        QtGui.QGraphicsView.keyReleaseEvent(self, event)

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
        """Zooming in and out"""
        if self.modifiers == QtCore.Qt.ControlModifier:
            self.scaleView(math.pow(2.0, +event.delta() / 240.0))
        elif self.modifiers == QtCore.Qt.ShiftModifier:
            self.viewCenter += QtCore.QPointF(-event.delta() / 2, 0)
            self.centerOn(self.viewCenter)
        else:
            self.viewCenter += QtCore.QPointF(0, -event.delta() / 2)
            self.centerOn(self.viewCenter)
        re = self.sceneRect()
        if self.viewCenter.y() > re.bottom() - (self.height() / 2):
            self.viewCenter.setY(re.bottom() - (self.height() / 2))
        elif self.viewCenter.y() < re.top() + (self.height() / 2):
            self.viewCenter.setY(re.top() + (self.height() / 2))
        if self.viewCenter.x() > re.right() - (self.width() / 2):
            self.viewCenter.setX(re.right() - (self.width() / 2))
        elif self.viewCenter.x() < re.left() + (self.width() / 2):
            self.viewCenter.setX(re.left() + (self.width() / 2))

    def scaleView(self, scaleFactor):
        factor = self.matrix().scale(scaleFactor, scaleFactor)
        factor = factor.mapRect(QtCore.QRectF(0, 0, 1, 1)).width()

        # heightsmaller = factor * self.sceneRect().y() < self.height()
        # widthsmaller = factor * self.sceneRect().x() < self.width()
        # if (heightsmaller and widthsmaller) or factor > 5:
        if factor < 0.2 or factor > 5:
            return

        self.scale(scaleFactor, scaleFactor)

    def addEdge(self, fromNode, toNode, multiselected=False):
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
        if multiselected:
            ed.multiselected = True
        self.edges.append(ed)
        self.scene.addItem(ed)

    def resetGraph(self):
        for item in self.nodes+self.edges:
            self.scene.removeItem(item)
        self.nodes = []
        self.edges = []

    def mousePressEvent(self, event):
        self.backgroundClick = True
        QtGui.QGraphicsView.mousePressEvent(self, event)
        if self.backgroundClick and event.button() == QtCore.Qt.LeftButton:
            self.pressedDown = True
            self.rubMoved = False
            self.origin = event.pos()
            self.rubberBand.setGeometry(QtCore.QRect(self.origin,
                                                     QtCore.QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        QtGui.QGraphicsView.mouseMoveEvent(self, event)
        if self.pressedDown:
            self.rubMoved = True
            self.rubrect = QtCore.QRect(self.origin, event.pos()).normalized()
            self.rubberBand.setGeometry(self.rubrect)

    def mouseReleaseEvent(self, event):
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        if self.pressedDown and self.rubMoved:
            self.rubberBand.hide()
            self.pressedDown = False
            rect = self.mapToScene(self.rubrect).boundingRect()
            for edge in self.edges:
                line = QtCore.QLineF(edge.sourcePoint, edge.destPoint)
                mid = line.pointAt(0.5).toPoint()
                if rect.contains(mid):
                    edge.multiselected = not edge.multiselected
                    edge.update()
            for node in self.nodes:
                bound = node.mapRectToScene(node.boundingRect()).toRect()
                if rect.contains(bound):
                    node.multiselected = not node.multiselected
                    node.update()

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

    def saveSnippet(self):
        """Turn the selected section of the node graph into a string"""
        tosave = {"nodes": {}, "edges": []}
        typest = ""
        for node in self.nodes:
            if node.selected or node.multiselected:
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
            if edge.selected or edge.multiselected:
                tosave["edges"].append({
                    "source": edge.source.UID,
                    "dest": edge.dest.UID
                })
        return tosave

    def load(self, toload):
        """Load from the text saved in the blend"""
        self.resetGraph()
        toparent = []
        for node in toload["nodes"]:
            lono = toload["nodes"][node]  # lono = alias for current node
            item = [x[1] for x in NODETYPES if x[0] == lono["type"]][0](self)
            if lono["type"] == "LogicNode":
                item.colour = logictypes[lono["category"][0]].colour
            else:
                item.colour = statetypes[lono["category"][0]].colour
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
            # TODO  I don't think this works
            if len(frame) > 0:
                frame[0].addChild(parent[0])
                parent[0].frameparent = frame[0]

        for edge in toload["edges"]:
            self.addEdge([x for x in self.nodes if x.UID == edge["dest"]][0],
                         [x for x in self.nodes if x.UID == edge["source"]][0])
        Rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(Rect)

    def insert(self, toload):
        """Load from the text saved in the blend"""
        clashChange = {}  # key: UID used to be, value: UID is now
        toparent = []
        for node in toload["nodes"]:
            lono = toload["nodes"][node]  # lono = alias for current node
            item = [x[1] for x in NODETYPES if x[0] == lono["type"]][0](self)
            if lono["type"] == "LogicNode":
                item.colour = logictypes[lono["category"][0]].colour
            else:
                item.colour = statetypes[lono["category"][0]].colour
            UID = self.getUID()
            clashChange[lono["UID"]] = UID
            item.UID = UID
            item.setPos(lono["posx"], lono["posy"])
            item.settings = lono["settings"]
            itse = item.settings
            item.displayname = lono["displayname"]
            for s in itse:
                if isinstance(itse[s], str):
                    itse[s] = itse[s].replace("{NEWLINE}", "\n")
            item.category = lono["category"]
            if lono["frameparent"][0]:
                toparent.append((item, lono["frameparent"][0]))
            item.multiselected = True
            self.nodes.append(item)
            self.scene.addItem(item)
        for parent in toparent:
            frame = [x for x in self.nodes if x.UID == clashChange[parent[1]]]
            if len(frame) > 0:
                frame[0].addChild(parent[0])
                parent[0].frameparent = frame[0]

        for edge in toload["edges"]:
            dest = clashChange[edge["dest"]]
            source = clashChange[edge["source"]]
            nodeUIDs = [x.UID for x in self.nodes]
            if source in nodeUIDs and dest in nodeUIDs:
                self.addEdge([x for x in self.nodes if x.UID == dest][0],
                             [x for x in self.nodes if x.UID == source][0],
                             multiselected=True)
        Rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(Rect)


# If this file isn't being imported do the following...
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    widget = CfxEditor(lambda x: print("Not connected"))
    widget.show()

    sys.exit(app.exec_())
