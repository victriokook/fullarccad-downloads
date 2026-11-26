"""SheetMetal is unavailable in this dependency-reduced release."""
from i18n import tr
AVAILABLE = False
COMMANDS = {}
def unavailable():
    raise RuntimeError(tr('この配布版では板金機能を提供していません。', 'Sheet metal features are unavailable in this release.'))
def load():
    unavailable()
def start(ws, key):
    unavailable()
