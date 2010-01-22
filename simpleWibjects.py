#   This file is part of VISVIS.
#    
#   VISVIS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as 
#   published by the Free Software Foundation, either version 3 of 
#   the License, or (at your option) any later version.
# 
#   VISVIS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
# 
#   You should have received a copy of the GNU Lesser General Public 
#   License along with this program.  If not, see 
#   <http://www.gnu.org/licenses/>.
#
#   Copyright (C) 2009 Almar Klein

""" Module simpleWibjects

Implements basic wibjects like buttons, and, maybe later, sliders etc.

$Author: almar.klein $
$Date: 2010-01-05 18:03:45 +0100 (di, 05 jan 2010) $
$Rev: 118 $

"""

import OpenGL.GL as gl

from events import BaseEvent
from misc import Property
from base import Box
from textRender import Label
from points import Pointset

# Note that we cannot include the Box and Label class here, since the latter
# depends on the first, and the BaseText class also needs the Label class.


class PushButton(Label):
    """ PushButton(parent, text='', fontname='sans')
    A button to click on. It is a label with an edgewidth of 1, in which
    text is horizontally aligned. Plus the hittest is put on by default.    
    """
    
    def __init__(self, parent, *args, **kwargs):
        Label.__init__(self, parent, *args, **kwargs)
        
        # Get an edge
        self.edgeWidth = 1
        
        # Text is centered by default
        self.halign = 0
        
        # A button is hittable by default
        self.hitTest = True


class ToggleButton(PushButton):
    """ ToggleButton(parent, text='', fontname='sans')
    Inherits from PushButton. This button can be set on and off by clicking
    on it, or by using it's property "state". The on state is indicated by
    making the edge thicker. The event eventStateChanged is fired when its
    state is changed.
    """
    
    def __init__(self, parent, *args, **kwargs):
        PushButton.__init__(self, parent, *args, **kwargs)
        
        # The state of the button, and an event to notify its change
        self._state = False
        self._eventStateChanged = BaseEvent(self)
        
        # Bind event
        self.eventMouseDown.Bind(self._OnDown)
    
    @Property
    def state():
        """ The state of the toggle button: on, or off.
        """
        def fset(self, value):
            self._state = bool(value)
            self._Update()
        def fget(self):
            return self._state
    
    @property
    def eventStateChanged(self):
        return self._eventStateChanged
    
    def _OnDown(self, event):
        self.state = not self.state
    
    def _Update(self, event=None):
        if self._state:
            self.edgeWidth = 2
        else:
            self.edgeWidth = 1        
        fig = self.GetFigure()
        if fig:
            fig.Draw()
        self._eventStateChanged.Fire()


class RadioButton(ToggleButton):
    """ RadioButton(parent, text='', fontname='sans')
    Inherits from ToggleButton. If pressed upon, sets the state of all
    sibling RadioButton instances to False, and its own state to True.
    
    When this happens, all instances will fire eventStateChanged (after
    the states are set). So it's only necessary to bind to one of them 
    to detect the selection of  another item.
    """
    
    def _OnDown(self, event):
        
        # Get me and all my siblings
        toggleButtons = []
        if self.parent:
            for sibling in self.parent.children:
                if isinstance(sibling, ToggleButton):
                    toggleButtons.append(sibling)
        
        # Disable all siblings (including self) and set own state
        for but in toggleButtons:
            but._state = False
        self._state = True
        
        # Update all so the events are fired
        for but in toggleButtons:
            but._Update()


class DraggableBox(Box):
    """ A Box wibject, but draggable and resizable. 
    Intended as a base class.
    """
    
    def __init__(self, parent):
        Box.__init__(self, parent)
        
        # Make me draggable
        self._dragStartPos = None
        self._dragResizing = False
        self._dragMouseOver = False
        
        # Prepare points to draw
        self._DragCalcDots()
        
        # Bind to own events
        self.hitTest = True
        self.eventMouseDown.Bind(self._DragOnDown)
        self.eventEnter.Bind(self._DragOnEnter)
        self.eventLeave.Bind(self._DragOnLeave)
        self.eventPosition.Bind(self._DragCalcDots)
        
        # Bind to figure events
        f = self.GetFigure()
        f.eventMotion.Bind(self._DragOnMove)
        f.eventMouseUp.Bind(self._DragOnUp)
    
    
    def _DragCalcDots(self, event=None):
        w,h = self.position.size
        dots = Pointset(2)
        #        
        dots.Append(3,3); dots.Append(3,6); dots.Append(3,9)
        dots.Append(6,3); dots.Append(6,6); dots.Append(6,9)
        dots.Append(9,3); dots.Append(9,6); dots.Append(9,9)
        #
        dots.Append(w-3, h-3); dots.Append(w-3, h-6); dots.Append(w-3, h-9)
        dots.Append(w-6, h-3); dots.Append(w-6, h-6);
        dots.Append(w-9, h-3);
        self._dots = dots
    
    def _DragOnEnter(self, event):
        self._dragMouseOver = True
        fig = self.GetFigure()
        if fig:
            fig.Draw()
    
    def _DragOnLeave(self, event):
        self._dragMouseOver = False
        fig = self.GetFigure()
        if fig:
            fig.Draw()
   
    def _DragOnDown(self, event):
        f = self.GetFigure()        
        pos = self.position
        # Store position if clicked on draggable arreas
        if event.x < 10 and event.y < 10:
            self._dragStartPos = f.mousepos[0],f.mousepos[1]
        elif event.x > pos.width-10 and event.y > pos.height-10:
            self._dragStartPos = f.mousepos[0],f.mousepos[1]
            self._dragResizing = True
    
    
    def _DragOnMove(self, event):        
        if not self._dragStartPos:
            return
        elif self._dragResizing:
            self.position.w += event.x - self._dragStartPos[0]
            self.position.h += event.y - self._dragStartPos[1]
            event.owner.Draw()
        else: # dragging
            self.position.x += event.x - self._dragStartPos[0]
            self.position.y += event.y - self._dragStartPos[1]
            event.owner.Draw()
        self._dragStartPos = event.x, event.y
    
    def _DragOnUp(self, event):
        self._DragOnMove(event)
        self._dragStartPos = None
        self._dragResizing = False
    
    
    def OnDraw(self):
        Box.OnDraw(self)
        
        if self._dragMouseOver:
            
            # Prepare
            gl.glColor(0,0,0,1)
            gl.glPointSize(1)
            gl.glDisable(gl.GL_POINT_SMOOTH)
            
            # Draw dots
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glVertexPointerf(self._dots.data)
            gl.glDrawArrays(gl.GL_POINTS, 0, len(self._dots))
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        