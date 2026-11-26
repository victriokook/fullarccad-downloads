"""Explicit local component BOM snapshots in a native Spreadsheet::Sheet."""
import json
import FreeCAD as App
import model,model_assembly
from i18n import tr
from bom_rows import group_rows


def collect(doc):
    if not doc or App.ActiveDocument is not doc:
        raise ValueError(tr('現在の文書を選択してください。','Use the active document.'))
    items=model_assembly.components(doc)
    if not 1<=len(items)<=2000:
        raise ValueError(tr('コンポーネントを1～2000個作成してください。','Create 1 to 2000 components first.'))
    records=[];stamp=[]
    for obj in items:
        model_assembly.valid_component(obj)
        source=obj.Source
        if not source or source.Document is not doc or source.getParentGeoFeatureGroup() and getattr(source,'FluxComponent',False):
            raise ValueError(tr('元ボディの参照を確認してください。','Check the source body reference.'))
        if getattr(source,'AssemblyError','') or 'Invalid' in source.State or 'Error' in source.State:
            raise ValueError(tr('元ボディにエラーがあります。','The source body has an error.'))
        model_assembly.local_shape(source)
        records.append((source.Name,source.Label,obj.Label))
        stamp.append((obj.Name,obj.Label,source.Name,source.Label,bool(obj.Grounded)))
    rows=group_rows(records)
    return rows,tuple(stamp)


def create(doc,expected=None):
    rows,stamp=collect(doc)
    if expected is not None and stamp!=expected:
        raise ValueError(tr('部品構成が変わりました。開き直してください。','Components changed. Reopen the dialog.'))
    headers=(tr('項目','Item'),tr('部品名','Part Name'),tr('元ボディID','Source Body ID'),tr('数量','Quantity'))
    with model.transaction(doc,tr('部品表を作成','Create Bill of Materials')):
        sheet=doc.addObject('Spreadsheet::Sheet','BillOfMaterials')
        sheet.Label=tr('部品表（スナップショット）','Bill of Materials (Snapshot)')
        for kind,name in [('App::PropertyBool','FluxBOM'),('App::PropertyString','BOMRowsJSON'),('App::PropertyInteger','BOMInstanceCount')]:
            sheet.addProperty(kind,name,'BOM')
        sheet.FluxBOM=True;sheet.BOMRowsJSON=json.dumps(rows,ensure_ascii=False);sheet.BOMInstanceCount=len(stamp)
        for name in ('FluxBOM','BOMRowsJSON','BOMInstanceCount'):sheet.setEditorMode(name,1)
        def literal(cell,value):sheet.set(cell,"'"+value)
        for col,value in zip('ABCD',headers):literal(col+'1',value)
        for rowno,(index,key,label,count) in enumerate(rows,2):
            sheet.set('A'+str(rowno),str(index));literal('B'+str(rowno),label)
            literal('C'+str(rowno),key);sheet.set('D'+str(rowno),str(count))
        sheet.setColumnWidth('A',60);sheet.setColumnWidth('B',240);sheet.setColumnWidth('C',180);sheet.setColumnWidth('D',80)
        sheet.setStyle('A1:D1','bold','add');sheet.setBackground('A1:D1',(0.14,0.24,0.33));sheet.setForeground('A1:D1',(1.0,1.0,1.0))
        doc.recompute()
        if 'Invalid' in sheet.State or 'Error' in sheet.State:raise ValueError('BOM spreadsheet failed')
        for rowno,(_,key,label,count) in enumerate(rows,2):
            if str(sheet.get('B'+str(rowno)))!=label or str(sheet.get('C'+str(rowno)))!=key or int(sheet.get('D'+str(rowno)))!=count:
                raise ValueError('BOM spreadsheet values do not match the validated rows')
    return sheet
