"""Cheap topology facts for the browser, invalidated by document changes.

Never build Python lists of all faces/edges just to ask whether one exists.
Only counts are cached; labels, visibility, operation flags and relationships
are still read by the browser on each refresh.
"""
import FreeCAD as App

_cache={}
_EMPTY=(False,0,0,0,0)

def invalidate(doc):
    if doc is not None:_cache.pop(doc.Name,None)

def facts(obj):
    doc=obj.Document
    if doc is None:return _EMPTY
    entry=_cache.get(doc.Name)
    if entry is None or entry[0] is not doc:
        entry=(doc,{});_cache[doc.Name]=entry
    saved=entry[1].get(obj.Name)
    if saved is not None and saved[0] is obj:return saved[1]
    shape=getattr(obj,'Shape',None)
    value=_EMPTY if shape is None else (True,)+tuple(shape.countElement(kind) for kind in ('Solid','Face','Edge','Vertex'))
    entry[1][obj.Name]=(obj,value)
    return value

def has_shape(obj):return facts(obj)[0]
def solids(obj):return facts(obj)[1]
def faces(obj):return facts(obj)[2]
def edges(obj):return facts(obj)[3]
def vertices(obj):return facts(obj)[4]

class Observer:
    def slotChangedObject(self,obj,prop):
        if prop in ('Shape','Group','Tip','LinkedObject','ElementList','LinkTransform',
                    'Links','Source','Sources','Objects','Base','Tool','Tools'):
            invalidate(obj.Document)
    def slotRecomputedObject(self,obj):invalidate(obj.Document)
    def slotCreatedObject(self,obj):invalidate(obj.Document)
    def slotDeletedObject(self,obj):invalidate(obj.Document)
    def slotDeletedDocument(self,doc):invalidate(doc)
    def slotUndoDocument(self,doc):invalidate(doc)
    def slotRedoDocument(self,doc):invalidate(doc)
    def slotFinishRestoreDocument(self,doc):invalidate(doc)

# The launcher reloads browser modules. Keep exactly one observer registered.
_previous=getattr(App,'_fullarc_browser_topology_observer',None)
if _previous is not None:App.removeDocumentObserver(_previous)
App._fullarc_browser_topology_observer=Observer()
App.addDocumentObserver(App._fullarc_browser_topology_observer)
