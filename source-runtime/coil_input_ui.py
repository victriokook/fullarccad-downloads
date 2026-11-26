"""Transient editor modes; never add document properties or change expression ownership."""
from PySide import QtWidgets as W
from i18n import tr
import parameters
from coil_input_math import resolve

def build(panel, field):
    panel.coil_mode_combo=field('coil_mode',tr('指定方法','Definition'),W.QComboBox())
    for ja,en,key in [('ピッチと巻き数','Pitch and Turns','pitch_turns'),('高さと巻き数','Height and Turns','height_turns'),('高さとピッチ','Height and Pitch','height_pitch')]:
        panel.coil_mode_combo.addItem(tr(ja,en),key)
    panel.coil_mode_combo.currentIndexChanged.connect(__import__('builtins')._fullarc_qt_slot(lambda: change_mode(panel),(0, 0, False, False)))

def linked(panel):
    return panel.existing is not None and any(parameters.expression(panel.existing,k) for k in ('Pitch','Turns'))

def baseline(panel, pitch, turns):
    panel.coil_canonical=(pitch,turns)
    panel.coil_exact={'pitch':pitch,'turns':turns,'height':pitch*turns}
    for key,value in panel.coil_exact.items():
        field=panel.fields[key];old=field.blockSignals(True)
        try:field.setValue(value)
        finally:field.blockSignals(old)
    panel.coil_shown={k:panel.fields[k].value() for k in panel.coil_exact}

def begin(panel, values):
    if panel.kind!='coil':return
    panel.coil_mode='pitch_turns';combo=panel.coil_mode_combo;old=combo.blockSignals(True)
    try:combo.setCurrentIndex(0)
    finally:combo.blockSignals(old)
    combo.setEnabled(not linked(panel))
    combo.setToolTip(tr('ピッチまたは巻き数が式で制御されている場合、指定方法は変更できません。','Definition is fixed when Pitch or Turns is controlled by an expression.'))
    baseline(panel,values['pitch'],values['turns'])

def apply(panel, result):
    if panel.kind!='coil':return result
    locked=linked(panel);panel.coil_mode_combo.setEnabled(not locked)
    if locked and panel.coil_mode!='pitch_turns':
        raise ValueError(tr('式の追加後はパネルを開き直してください。','Reopen the panel after adding an expression.'))
    if locked:return result
    keys={'pitch_turns':('pitch','turns'),'height_turns':('height','turns'),'height_pitch':('height','pitch')}[panel.coil_mode]
    shown={k:panel.fields[k].value() for k in keys}
    if all(shown[k]==panel.coil_shown[k] for k in keys):pitch,turns=panel.coil_canonical
    else:
        values=dict(panel.coil_exact)
        for k in keys:values[k]=panel.coil_exact[k] if shown[k]==panel.coil_shown[k] else shown[k]
        pitch,turns=resolve(panel.coil_mode,values['pitch'],values['turns'],values['height'])
    result.update(pitch=pitch,turns=turns)
    return result

def change_mode(panel):
    if not panel.active or panel.kind!='coil':return
    old_mode=panel.coil_mode
    try:
        for k in ('pitch','turns','height'):panel.fields[k].interpretText()
        values=panel.parameters()
        panel.coil_mode=panel.coil_mode_combo.currentData()
        baseline(panel,values['pitch'],values['turns'])
        panel.update_preview()
    except Exception as error:
        old=panel.coil_mode_combo.blockSignals(True)
        try:panel.coil_mode_combo.setCurrentIndex(panel.coil_mode_combo.findData(old_mode))
        finally:panel.coil_mode_combo.blockSignals(old)
        panel.coil_mode=old_mode;panel.clear_preview();panel.valid=False
        panel.accept_button.setEnabled(False);panel.status.setText(str(error))

def visible_keys(panel, keys):
    if panel.kind!='coil':return keys
    keys=set(keys);keys.add('coil_mode')
    if panel.coil_mode=='height_turns':keys.discard('pitch');keys.add('height')
    elif panel.coil_mode=='height_pitch':keys.discard('turns');keys.add('height')
    return keys
