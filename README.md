# Network Subgraph Metrics Dashboard
This Python project generates a dashboard and CSV report that show how many subgraphs are deployed per network on [The Graph Network](https://thegraph.com). It includes time-based metrics, daily snapshots, and a modern, responsive HTML interface.

**Live Dashboard:**  
🔗 [graphtools.pro/network](https://graphtools.pro/network)

🧪 This dashboard is part of [**Graph Tools Pro**](https://graphtools.pro), a community-driven initiative to provide useful, independent analytics tools for The Graph ecosystem.

---

## 📊 Features

- Daily fetch of subgraph counts per network
- HTML dashboard with light/dark theme
- CSV export of all network counts
- 24-hour delta tracking (if yesterday’s snapshot exists)
- Custom network logos
- JSON snapshot stored daily with timestamp and counts
- Full logs of script runs

---

## 📂 Project Structure
📦 network/
- 📜 fetch_network_metrics.py         # Main script
- 📜 .env                             # Environment variables (not tracked)
- 📂 logs/                            # Timestamped log files
- 📂 reports/
  - 📜 index.html                    # Rendered dashboard
  - 📜 network_subgraph_counts.csv   # CSV report
- 📂 metrics/                        # JSON metric snapshots per day
---

## 🚀 How to Run

1. Install dependencies:
`pip install requests python-dotenv`

2.	Create a .env file:
`
GRAPH_API_KEY=your_graph_api_key
METRIC_SNAPSHOT_HOUR=8
`

3.	Run the script:
`python fetch_network_metrics.py`

4. Open `reports/index.html` in your browser to view the dashboard.

## 📊 Powered By
- 🧠 [The Graph](https://thegraph.com)
- 🧩 Python 3.x, HTML5 + CSS 
- ⚙️ Data sorting and light/dark theming via vanilla JavaScript
