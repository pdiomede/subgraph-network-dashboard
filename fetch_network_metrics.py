import os
import json
import csv
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List


# v1.0.5 / 14-May-2025
# Author: Paolo Diomede
DASHBOARD_VERSION = "1.0.5"


# Data class for network subgraph counts
@dataclass
class NetworkSubgraphCount:
    network_name: str
    subgraph_count: int

# Data class for network subgraph and unique indexer counts
from collections import namedtuple
NetworkIndexerData = namedtuple("NetworkIndexerData", ["network_name", "subgraph_count", "unique_indexer_count"])

# Mapping of network names to local logo image paths
NETWORK_LOGOS = {
    "abstract": "images/abstract.png",
    "arbitrum-nova": "images/arbitrum-nova.png",
    "arbitrum-one": "images/arbitrum.png",
    "aurora": "images/aurora.png",
    "avalanche": "images/avalanche.png",
    "base": "images/base.png",
    "berachain": "images/berachain.png",
    "blast": "images/blast.png",
    "boba": "images/boba.png",
    "bsc": "images/bsc.png",
    "celo": "images/celo.png",
    "chiliz": "images/chiliz.png",
    "corn": "images/corn.png",
    "eos": "images/eos.png",
    "etherlink": "images/etherlink.png",
    "fantom": "images/fantom.png",
    "fraxtal": "images/fraxtal.png",
    "fuji": "images/fuji.png",
    "fuse": "images/fuse.png",
    "gnosis": "images/gnosis.png",
    "harmony": "images/harmony.png",
    "hemi": "images/hemi.png",
    "injective": "images/injective.png",
    "ink": "images/ink.png",
    "iotex": "images/iotex.png",
    "kaia": "images/kaia.png",
    "kroma": "images/kroma.png",
    "kylin": "images/kylin.png",
    "lens": "images/lens.png",
    "lens-2": "images/lens-2.png",
    "linea": "images/linea.png",
    "mainnet": "images/ethereum.png",
    "mantle": "images/mantle.png",
    "matic": "images/polygon.png",
    "monad": "images/monad.png",
    "moonbeam": "images/moonbeam.png",
    "near": "images/near.png",
    "optimism": "images/optimism.png",
    "polygon-zkevm": "images/polygon-zkevm.png",
    "redstone": "images/redstone.png",
    "rootstock": "images/rootstock.png",
    "scroll": "images/scroll.png",
    "sei": "images/sei.png",
    "sepolia": "images/sepolia.png",
    "soneium": "images/soneium.png",
    "sonic": "images/abstract.png",
    "unichain": "images/unichain.png",
    "vana": "images/vana.png",
    "wax": "images/wax.png",
    "zkfair": "images/zkfair.png",
    "zksync-era": "images/zksync-era.png",
    "zetachain": "images/zetachain.png"
}


# Function that writes in the log file
def log_message(message):
    timestamped = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] {message}"
    print(timestamped)
    with open(log_file, "a") as log:
        log.write(timestamped + "\n")
# End Function 'log_message'


# Load environment variables from the .env file
load_dotenv()
API_KEY = os.getenv("GRAPH_API_KEY")

# Load metric snapshot target hour from environment, default to 8
METRIC_SNAPSHOT_HOUR = int(os.getenv("METRIC_SNAPSHOT_HOUR", 8))

# List of all used subgraphs
SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/9wzatP4KXm4WinEhB31MdKST949wCH8ZnkGe8o3DLTwp"

# Create REPORTS directory if it doesn't exist
report_dir = "reports"
os.makedirs(report_dir, exist_ok=True)

# Create LOGS directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"metrics_log_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.txt")

# Create METRICS directory if it doesn't exist
metrics_dir = "./reports/metrics"
os.makedirs(metrics_dir, exist_ok=True)

# Get data to be used in the log and report files
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def fetch_network_subgraph_counts() -> List["NetworkIndexerData"]:
    """Fetch network names and count subgraphs and unique indexers per network using updated query"""
    url = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
    headers = {"Content-Type": "application/json"}
    counts = {}
    indexers_by_network = {}
    skip = 0
    page_size = 1000

    while True:
        query = f"""{{
            subgraphs(first: {page_size}, skip: {skip}, where: {{ currentVersion_not: null }}) {{
                id
                currentVersion {{
                    subgraphDeployment {{
                        manifest {{
                            network
                        }}
                        indexerAllocations(first: 1000, where: {{ status: Active }}) {{
                            indexer {{
                                id
                            }}
                        }}
                    }}
                }}
            }}
        }}"""

        response = requests.post(url, json={"query": query}, headers=headers)

        if response.status_code != 200:
            log_message(f"Failed to fetch data: {response.status_code}")
            break

        batch = response.json().get("data", {}).get("subgraphs", [])
        if not batch:
            break

        for item in batch:
            deployment = item.get("currentVersion", {}).get("subgraphDeployment", {})
            manifest = deployment.get("manifest")
            if not manifest:
                continue
            network = manifest.get("network")
            if not network:
                continue
            counts[network] = counts.get(network, 0) + 1
            # Process indexerAllocations
            allocations = deployment.get("indexerAllocations", [])
            if network not in indexers_by_network:
                indexers_by_network[network] = set()
            for alloc in allocations:
                indexer = alloc.get("indexer")
                if indexer and "id" in indexer:
                    indexers_by_network[network].add(indexer["id"])

        skip += page_size

    result = []
    for network, subgraph_count in counts.items():
        unique_indexer_count = len(indexers_by_network.get(network, set()))
        result.append(NetworkIndexerData(network_name=network, subgraph_count=subgraph_count, unique_indexer_count=unique_indexer_count))
    log_message(f"Fetched subgraph and indexer counts for {len(result)} networks.")
    return result


def save_subgraph_counts_to_csv(data: List[NetworkIndexerData], filename: str = "network_subgraph_counts.csv"):
    path = os.path.join(report_dir, filename)
    # Sort data in descending order by subgraph_count before writing
    sorted_data = sorted(data, key=lambda x: x.subgraph_count, reverse=True)
    with open(path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Network", "Subgraph Count", "Unique Indexers"])
        for entry in sorted_data:
            if entry.network_name.lower() == "mainnet":
                name = "Ethereum (Mainnet)"
            elif entry.network_name.lower() == "matic":
                name = "Polygon (Matic)"
            else:
                name = entry.network_name
            writer.writerow([name, f"{entry.subgraph_count:,}", entry.unique_indexer_count])
    log_message(f"Saved CSV report to {path}")


def save_subgraph_counts_to_html(data: List[NetworkIndexerData], filename: str = "index.html", total_subgraphs_yesterday=None, yesterday_network_counts=None):
    path = os.path.join(report_dir, filename)
    total = sum(entry.subgraph_count for entry in data)
    sorted_data = sorted(data, key=lambda x: x.subgraph_count, reverse=True)

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Explore a real-time dashboard showing the number of subgraphs published on The Graph Network across supported blockchain networks.">
        <meta name="robots" content="index, follow">

        <meta property="og:title" content="Graph Tools Pro :: Subgraphs per Network">
        <meta property="og:description" content="Visualize how many subgraphs are deployed per chain on The Graph Network with this interactive dashboard.">
        <meta property="og:url" content="https://graphtools.pro/delegators/">
        <meta property="og:type" content="website">
        <meta property="og:image" content="https://graphtools.pro/graphtoolsprologo.jpg">
        
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Graph Tools Pro :: Delegators Activity Log">
        <meta name="twitter:description" content="See how The Graph Network is utilized across different chains through a live subgraph deployment tracker.">
        <meta name="twitter:image" content="https://graphtools.pro/graphtoolsprologo.jpg">
        
        <title>Graph Tools Pro: Subgraphs Network Dashboard</title>
        <link rel="icon" type="image/png" href="https://graphtools.pro/favicon.ico">
        
        <style>           
            :root {{
                --bg-color: #111;
                --text-color: #fff;
                --table-bg: #1e1e1e;
                --header-bg: #333;
                --link-color: #fff;
                --table-border-color: #444;
                --row-border-color: rgba(255, 255, 255, 0.08); /* Default for dark mode */
            }}
            .light-mode {{
                --bg-color: #f0f2f5;
                --text-color: #000;
                --table-bg: #ffffff;
                --header-bg: #ddd;
                --link-color: #0000EE;
                --table-border-color: #ccc;
                --row-border-color: rgba(0, 0, 0, 0.3); /* Increased opacity for better visibility in light mode */
            }}
            /* Lighter border and shadow for light mode */
            .light-mode table {{
                border-color: #ccc;
                box-shadow: 0 0 0 1px #ccc, 0 0 8px rgba(0, 0, 0, 0.08);
            }}
            .light-mode .home-link {{
                color: var(--text-color);
            }}
            body {{
                background-color: var(--bg-color);
                color: var(--text-color);
                font-family: Arial, sans-serif;
                padding: 10px 20px 20px 20px;
                margin-top: 0;
                transition: all 0.3s ease;
            }}
            .header-container {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                line-height: 1;
            }}
            .breadcrumb {{
                font-size: 0.9em;
                margin: 0;
                padding: 0;
                display: flex;
                align-items: center;
            }}
            .toggle-container {{
                display: flex;
                align-items: center;
                margin: 0;
                padding: 0;
            }}
            .toggle-switch {{
                position: relative;
                width: 50px;
                height: 24px;
                margin-right: 10px;
            }}
            .toggle-switch input {{
                opacity: 0;
                width: 0;
                height: 0;
            }}
            .toggle-switch .slider {{
                position: absolute;
                top: 0; left: 0;
                right: 0; bottom: 0;
                background: #ccc;
                transition: 0.4s;
                border-radius: 34px;
            }}
            .toggle-switch .slider:before {{
                position: absolute;
                content: "";
                height: 18px;
                width: 18px;
                left: 4px;
                bottom: 3px;
                background: white;
                transition: 0.4s;
                border-radius: 50%;
            }}
            .toggle-switch input:checked + .slider {{
                background: #2196F3;
            }}
            .toggle-switch input:checked + .slider:before {{
                transform: translateX(24px);
            }}
            #toggle-icon {{
                font-size: 1.5rem;
                line-height: 1;
            }}
            .divider {{
                border: 0;
                height: 2px;
                background: linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0));
                margin: 15px 0;
            }}
            .light-mode .divider {{
                background: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0));
            }}
            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                background: var(--table-bg);
                border: 1px solid var(--table-border-color);
                box-shadow: 0 0 0 1px var(--table-border-color);
                border-radius: 12px;
                overflow: hidden;
            }}
            th, td {{
                padding: 8px 12px;
                border: none;
                text-align: left;
            }}
            td {{
                border-bottom: 1px solid var(--row-border-color);
            }}
            th {{
                background-color: var(--header-bg);
                color: var(--text-color);
            }}
            tr:last-child td {{
                border-bottom: none;
            }}
            .download-button {{
                padding: 5px 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }}
            .download-button:hover {{
                background-color: #45a049;
            }}
            .tooltip-header {{
                position: relative;
                cursor: help;
            }}
            .tooltip-header .tooltip-text {{
                visibility: hidden;
                background-color: #333;
                color: #ffeb3b;
                text-align: left;
                padding: 6px 10px;
                border-radius: 4px;
                position: absolute;
                z-index: 9999;
                top: 135%;
                right: auto;
                left: 50%;
                transform: translateX(-50%);
                opacity: 0;
                transition: opacity 0.3s;
                width: max-content;
                max-width: 220px;
                font-size: 13px;
                pointer-events: none;
                overflow: visible;
                white-space: normal;
                word-wrap: break-word;
                box-sizing: border-box;
            }}
            .tooltip-header:hover .tooltip-text {{
                visibility: visible;
                opacity: 1;
            }}
            a {{
                color: var(--link-color);
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                text-align: center;
                margin: 10px 0 40px;
                font-size: 0.9rem;
                opacity: 0.9;
            }}
            .footer a {{
                color: #80bfff;
                text-decoration: none;
                transition: color 0.3s ease;
            }}
            .footer a:hover {{
                color: #4d94ff;
            }}
            .light-mode .footer a {{
                color: #0066cc;
            }}
            .light-mode .footer a:hover {{
                color: #0033ff;
            }}
            .footer-divider {{
                border: none;
                border-bottom: 1px solid rgba(200, 200, 200, 0.2);
                margin: 40px 0 10px;
                opacity: 0.8;
            }}
            .current-page-title {{
                color: #00bcd4;
                font-weight: bold;
            }}
            .light-mode .current-page-title {{
                color: #1a73e8;
            }}
        </style>
    </head>

    <body>

        <!-- Header with breadcrumb and toggle -->

        <div class="header-container">
            <div class="breadcrumb" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 500; font-size: 0.85em; letter-spacing: 0.3px; text-shadow: 0 1px 2px rgba(0,0,0,0.15);">
                <a href="https://graphtools.pro" class="home-link" style="text-decoration: none;">🏠 Home</a>&nbsp;&nbsp;&raquo;&nbsp;&nbsp;
                <span class="current-page-title">📊 Subgraphs Network Dashboard</span>    
            </div>

            <div class="toggle-container">
                <label class="toggle-switch">
                    <input type="checkbox" onclick="toggleTheme()">
                    <span class="slider"></span>
                </label>
                <span id="toggle-icon">🌙</span>
            </div>

        </div>

        <hr class="divider">
            <div style="text-align: center;">    
            <h1 style="margin-bottom: 4px;">Subgraphs Network Dashboard</h1>
            <div style="text-align: center; font-size: 0.8em; color: var(--text-color); margin-top: 0; margin-bottom: 30px;">
                Generated on: {timestamp} - (updated every day at 8am UTC) - v{DASHBOARD_VERSION}
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; max-width: 600px; margin: 0 auto 10px auto; font-size: 1em;">
            <div style="color: #4CAF50;"><strong>Total Subgraphs:</strong> {total:,}{f" ({total - total_subgraphs_yesterday:+,} since yesterday)" if total_subgraphs_yesterday is not None else ""}</div>
            <button class="download-button" onclick="downloadCSV()">Download CSV</button>
        </div>
        <div style="overflow-x:auto; max-width: 600px; margin: 0 auto;">
        <table id="networkTable" style="width: 100%;">
            <tr>
                <th onclick="sortTable(0)" style="cursor:pointer;" data-sort-direction="desc">
                    <span class="tooltip-header" style="position: relative; display: inline-block;">
                        Network
                    </span>
                </th>
                <th onclick="sortTable(1)" style="cursor:pointer;" data-sort-direction="desc">
                    <span class="tooltip-header" style="position: relative; display: inline-block;">
                        Subgraph Count
                        <span class="tooltip-text">Total number of subgraphs currently deployed on this network</span>
                    </span>
                </th>
                <th onclick="sortTable(2)" style="cursor:pointer;" data-sort-direction="desc">
                    <span class="tooltip-header" style="position: relative; display: inline-block;">
                        Var (24h)
                        <span class="tooltip-text">Change in subgraph count compared to the previous day</span>
                    </span>
                </th>
                <th onclick="sortTable(3)" style="cursor:pointer;" data-sort-direction="desc">
                    <span class="tooltip-header" style="position: relative; display: inline-block;">
                        Unique Indexers
                        <span class="tooltip-text">Number of unique indexers actively allocating to this network</span>
                    </span>
                </th>
            </tr>"""

    for entry in sorted_data:
        logo = NETWORK_LOGOS.get(entry.network_name.lower(), "")
        logo_html = f"<img src='{logo if logo else 'images/placeholder_logo.png'}' alt='{entry.network_name}' style='width:18px; height:18px; vertical-align:middle; margin-right:6px;' />"
        if entry.network_name.lower() == "mainnet":
            name = "Ethereum (Mainnet)"
        elif entry.network_name.lower() == "matic":
            name = "Polygon (Matic)"
        else:
            name = entry.network_name.title()
        diff = ""
        diff_value = ""
        if yesterday_network_counts:
            yesterday_val = yesterday_network_counts.get(entry.network_name, 0)
            change = entry.subgraph_count - yesterday_val
            if change > 0:
                diff = f"<span style='color: #4CAF50; font-size: 0.85em;'>{change:+}</span>"
            elif change < 0:
                diff = f"<span style='color: #f44336; font-size: 0.85em;'>{change:+}</span>"
            diff_value = str(change)
        html += f"""
            <tr>
              <td>{logo_html}<a href="https://thegraph.com/explorer?indexedNetwork={entry.network_name}&orderBy=Query+Count&orderDirection=desc" target="_blank" style="color: var(--link-color); text-decoration: none;">{name} <img src="./images/link-icon.png" alt="link icon" style="width: 12px; height: 12px; vertical-align: middle; margin-left: 4px;" /></a></td>
                <td data-value="{entry.subgraph_count}">{entry.subgraph_count:,}</td>
                <td data-value="{diff_value}">{diff}</td>
                <td data-value="{entry.unique_indexer_count}">{entry.unique_indexer_count}</td>
            </tr>"""

    html += """
        </table>

            <hr class="footer-divider">
            <div class="footer">
                ©<script>document.write(new Date().getFullYear())</script> 
                <a href="https://graphtools.pro">Graph Tools Pro</a> :: Made with ❤️ by 
                <a href="https://x.com/graphtronauts_c" target="_blank">Graphtronauts</a>
                for <a href="https://x.com/graphprotocol" target="_blank">The Graph</a> ecosystem 👨‍🚀
                <div style="margin-top: 4px;">
                    <span style="font-size: 0.8rem;">For Info: <a href="https://x.com/pdiomede" target="_blank">@pdiomede</a> & <a href="https://x.com/PaulBarba12" target="_blank">@PaulBarba12</a></span>
                </div>
            </div>
        
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const toggle = document.getElementById('themeToggle');
                const body = document.body;
                // Default to dark mode
                body.classList.add('dark-mode');

                toggle.addEventListener('change', () => {
                    body.classList.toggle('dark-mode');
                    body.classList.toggle('light-mode');
                });
            });

            function toggleTheme() {
                document.body.classList.toggle('light-mode');
                const icon = document.getElementById('toggle-icon');
                icon.textContent = document.body.classList.contains('light-mode') ? '☀️' : '🌙';
            }
                
            function sortTable(columnIndex) {
                const table = document.getElementById("networkTable");
                const rows = Array.from(table.rows).slice(1);
                const isNumeric = columnIndex === 1 || columnIndex === 3;
                const header = table.rows[0].cells[columnIndex];
                const currentDirection = header.getAttribute("data-sort-direction") || "desc";
                const newDirection = currentDirection === "asc" ? "desc" : "asc";
                header.setAttribute("data-sort-direction", newDirection);

                Array.from(table.rows[0].cells).forEach((cell, idx) => {
                    if (idx != columnIndex) {
                        cell.removeAttribute("data-sort-direction");
                    }
                });

                rows.sort((a, b) => {
                    let aVal = a.cells[columnIndex].getAttribute("data-value") || a.cells[columnIndex].textContent.trim();
                    let bVal = b.cells[columnIndex].getAttribute("data-value") || b.cells[columnIndex].textContent.trim();
                    if (isNumeric) {
                        aVal = parseFloat(aVal.replace(/,/g, '')) || 0;
                        bVal = parseFloat(bVal.replace(/,/g, '')) || 0;
                    }
                    return (newDirection === "asc" ? aVal > bVal : aVal < bVal) ? 1 : -1;
                });

                rows.forEach(row => table.tBodies[0].appendChild(row));
            }
            function downloadCSV() {
                const link = document.createElement('a');
                link.href = 'network_subgraph_counts.csv';
                link.download = 'network_subgraph_counts.csv';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        </script>
    </body>
    </html>
    """

    with open(path, mode="w", encoding="utf-8") as file:
        file.write(html)

    log_message(f"Saved HTML report to {path}")


if __name__ == "__main__":
    log_message("Starting network subgraph metrics script...")
    log_message(f"🕒 Configured METRIC_SNAPSHOT_HOUR: {METRIC_SNAPSHOT_HOUR}")
    subgraph_data = fetch_network_subgraph_counts()
    if subgraph_data:
        # Only write metrics at the configured UTC hour
        current_time_utc = datetime.now(timezone.utc)

        # Look for yesterday's metric file and read total_subgraphs
        yesterday_date = (current_time_utc - timedelta(days=1)).strftime('%Y%m%d')
        yesterday_file = None
        for file in os.listdir(metrics_dir):
            if file.startswith(f"metric_{yesterday_date}"):
                yesterday_file = os.path.join(metrics_dir, file)
                break

        total_subgraphs_yesterday = None
        yesterday_network_counts = None
        
        if yesterday_file:
            try:
                with open(yesterday_file, "r") as f:
                    yesterday_data = json.load(f)
                    total_subgraphs_yesterday = int(yesterday_data.get("total_subgraphs", 0))
                    log_message(f"✅ Parsed total_subgraphs_yesterday as {total_subgraphs_yesterday}")
                    yesterday_network_counts = yesterday_data.get("networks", {})
            except Exception as e:
                log_message(f"⚠️ Failed to load yesterday's metric file: {e}")
                yesterday_network_counts = None
        else:
            log_message("📭 No metric file found for yesterday.")
            yesterday_network_counts = None

        if METRIC_SNAPSHOT_HOUR <= current_time_utc.hour < METRIC_SNAPSHOT_HOUR + 1:
            # Save metrics snapshot
            total_subgraphs = sum(entry.subgraph_count for entry in subgraph_data)
            # --- Logging total subgraphs today/yesterday
            log_message(f"📅 Total Subgraphs Today: {total_subgraphs}")
            if total_subgraphs_yesterday is not None:
                log_message(f"📆 Total Subgraphs Yesterday: {total_subgraphs_yesterday}")
            else:
                log_message("📆 Total Subgraphs Yesterday: unavailable")

            metrics_snapshot = {
                "timestamp": current_time_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "total_subgraphs": total_subgraphs,
                "networks": {entry.network_name: entry.subgraph_count for entry in subgraph_data}
            }

            metric_filename = f"metric_{current_time_utc.strftime('%Y%m%d_%H%M%S')}.json"
            metric_path = os.path.join(metrics_dir, metric_filename)
            with open(metric_path, "w") as metric_file:
                json.dump(metrics_snapshot, metric_file, indent=2)
            log_message(f"📁 Saved metrics snapshot to {metric_path}")
        else:
            log_message(f"⏩ Skipped metric snapshot creation — not {METRIC_SNAPSHOT_HOUR:02d}:00 UTC.")

        save_subgraph_counts_to_csv(subgraph_data)
        save_subgraph_counts_to_html(subgraph_data, total_subgraphs_yesterday=total_subgraphs_yesterday, yesterday_network_counts=yesterday_network_counts)
    else:
        log_message("No data retrieved.")
