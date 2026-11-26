"""Localized UI text; language changes take effect on restart."""
import FreeCAD as App
from translations_en import EN
from translations_de import DE
from translations_ko import KO
from translations_it import IT
from translations_pt_br import PT_BR
from translations_es import ES
from translations_fr import FR
from translations_zh_cn import ZH_CN
from translations_zh_tw import ZH_TW
from product_brand import display

PREFERENCES='User parameter:BaseApp/Preferences/FluxCAD'
# Add a reviewed catalog here to expose a language in the settings menu.
# Each catalog maps original Japanese messages to localized display text.
LANGUAGES = {
    'ja': {'label': '日本語', 'freecad': 'Japanese', 'catalog': {}},
    'en': {'label': 'English', 'freecad': 'English', 'catalog': EN},
    'de': {'label': 'Deutsch', 'freecad': 'German', 'catalog': DE},
    'zh-TW': {'label': '繁體中文（台灣）', 'freecad': 'Chinese (Traditional)', 'catalog': ZH_TW},
    'es': {'label': 'Español', 'freecad': 'Spanish', 'catalog': ES},
    'fr': {'label': 'Français', 'freecad': 'French', 'catalog': FR},
    'zh-CN': {'label': '简体中文', 'freecad': 'Chinese (Simplified)', 'catalog': ZH_CN},
    'ko': {'label': '한국어', 'freecad': 'Korean', 'catalog': KO},
    'it': {'label': 'Italiano', 'freecad': 'Italian', 'catalog': IT},
    'pt-BR': {'label': 'Português (Brasil)', 'freecad': 'Portuguese (Brazilian)', 'catalog': PT_BR},
}
_language=App.ParamGet(PREFERENCES).GetString('Language','ja')
if _language not in LANGUAGES:_language='ja'


def available_languages():
    return tuple((code, info['label']) for code, info in LANGUAGES.items())


def language():
    return _language


def tr(source, english=None):
    """Translate a display string, with an optional contextual English form."""
    if _language == 'ja':return display(source)
    fallback = english if english is not None else EN.get(source, source)
    if _language == 'en':return display(fallback)
    return display(LANGUAGES[_language]['catalog'].get(source, fallback))


def pending_language():
    result=App.ParamGet(PREFERENCES).GetString('Language',_language)
    return result if result in LANGUAGES else _language


def save_language(code):
    if code not in LANGUAGES:raise ValueError('Unsupported language: '+str(code))
    App.ParamGet(PREFERENCES).SetString('Language',code)
    # FreeCAD reads this preference on its next launch, including its native
    # Sketcher tasks. Never rebuild the workspace while a document is edited.
    App.ParamGet('User parameter:BaseApp/Preferences/General').SetString('Language',LANGUAGES[code]['freecad'])
    App.saveParameter()
