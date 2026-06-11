from PyQt5.QtWidgets import QApplication
import sys
import time

from pathlib import Path
import sys
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui.dashboard.main import SystemMonitor

app = QApplication(sys.argv)
win = SystemMonitor()
# Try different sizes
sizes = [(1200, 780), (900, 600), (700, 480), (500, 360)]
results = []
for w, h in sizes:
    win.resize(w, h)
    win.show()
    app.processEvents()
    time.sleep(0.25)
    try:
        overview_index = None
        for i in range(win.main_tabs.count()):
            if win.main_tabs.tabText(i).lower().startswith('overview'):
                overview_index = i
                break
        if overview_index is None:
            print('Overview tab not found')
            continue
        win.main_tabs.setCurrentIndex(overview_index)
        app.processEvents()
        time.sleep(0.25)
        # access overview widget
        overview_widget = win.main_tabs.widget(overview_index)
        geo = overview_widget.geometry()
        # collect sizes of first row cards
        card_sizes = []
        try:
            # find QFrame children
            frames = overview_widget.findChildren(type(win.cpu_label.parent()))
        except Exception:
            frames = overview_widget.findChildren(type(win.cpu_label))
        # fallback: find known labels and parent
        for label_name in ['cpu_label', 'gpu_label', 'memory_label', 'disk_label', 'eth_label', 'process_label']:
            lbl = getattr(win, label_name, None)
            if lbl is None:
                card_sizes.append(('missing', 0, 0))
                continue
            parent = lbl.parent()
            if parent is None:
                card_sizes.append((label_name, 0, 0))
            else:
                card_sizes.append((label_name, parent.width(), parent.height()))
        print(f"SIZE {w}x{h}: overview {geo.width()}x{geo.height()} cards: {card_sizes}")
    except Exception as e:
        print('Error during size check:', e)

# exit
print('DONE')
win.close()
app.exit()
