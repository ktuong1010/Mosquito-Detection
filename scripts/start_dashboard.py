import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dashboard import app
from config import DASHBOARD_HOST, DASHBOARD_PORT

if __name__ == '__main__':
    print("=" * 70)
    print("Mosquito Density Dashboard")
    print("=" * 70)
    print(f"Starting server on http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False)

