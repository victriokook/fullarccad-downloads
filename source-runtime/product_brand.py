"""FullArcCAD display branding; legacy storage identifiers remain compatible."""
APP_NAME='FullArcCAD'
def display(text):return text.replace('FluxCAD',APP_NAME)

def install(main):
    from PySide import QtCore,QtWidgets as W
    app=W.QApplication.instance();existing=getattr(app,'_fullarc_brand_filter',None)
    if existing is not None:existing.main=main;existing.update(main);return existing
    class BrandFilter(QtCore.QObject):
        def __init__(self):super().__init__(app);self.main=main;self.changing=False
        def update(self,obj):
            if self.changing:return
            try:
                title=obj.windowTitle()
                updated=(APP_NAME+' — '+title) if obj is self.main and not title.startswith(APP_NAME+' — ') else display(title) if isinstance(obj,W.QDialog) and 'FluxCAD' in title else title
                if updated!=title:
                    self.changing=True
                    try:obj.setWindowTitle(updated)
                    finally:self.changing=False
            except RuntimeError:pass
        def eventFilter(self,obj,event):
            if event.type() in (QtCore.QEvent.Show,QtCore.QEvent.WindowTitleChange) and (obj is self.main or isinstance(obj,W.QDialog)):self.update(obj)
            return False
    watcher=BrandFilter();app._fullarc_brand_filter=watcher;app.installEventFilter(watcher);watcher.update(main);return watcher
