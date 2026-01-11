from flask import Flask, render_template_string, jsonify
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, DASHBOARD_HOST, DASHBOARD_PORT
from src.visualization import DensityAnalyzer

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mosquito Density Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #666;
        }
        .stat-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .chart-container {
            margin: 30px 0;
            position: relative;
            height: 400px;
        }
        .chart-container h2 {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mosquito Density Dashboard</h1>
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Aedes</h3>
                <div class="value" id="aedes-count">0</div>
                <div>Avg Confidence: <span id="aedes-conf">0%</span></div>
            </div>
            <div class="stat-card">
                <h3>Culex</h3>
                <div class="value" id="culex-count">0</div>
                <div>Avg Confidence: <span id="culex-conf">0%</span></div>
            </div>
            <div class="stat-card">
                <h3>Total</h3>
                <div class="value" id="total-count">0</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Daily Density</h2>
            <canvas id="dailyChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2>Weekly Summary</h2>
            <canvas id="weeklyChart"></canvas>
        </div>
    </div>
    
    <script>
        const days = 7;
        let dailyChart, weeklyChart;
        
        function loadData() {
            fetch(`/api/data?days=${days}`)
                .then(response => response.json())
                .then(data => {
                    updateStats(data.stats);
                    updateDailyChart(data.daily);
                    updateWeeklyChart(data.weekly);
                });
        }
        
        function updateStats(stats) {
            const aedes = stats.Aedes || {total_count: 0, avg_confidence: 0};
            const culex = stats.Culex || {total_count: 0, avg_confidence: 0};
            const total = aedes.total_count + culex.total_count;
            
            document.getElementById('aedes-count').textContent = aedes.total_count;
            document.getElementById('aedes-conf').textContent = (aedes.avg_confidence * 100).toFixed(1) + '%';
            document.getElementById('culex-count').textContent = culex.total_count;
            document.getElementById('culex-conf').textContent = (culex.avg_confidence * 100).toFixed(1) + '%';
            document.getElementById('total-count').textContent = total;
        }
        
        function updateDailyChart(data) {
            const ctx = document.getElementById('dailyChart').getContext('2d');
            
            if (dailyChart) {
                dailyChart.destroy();
            }
            
            const dates = data.map(d => d.date);
            const aedes = data.map(d => d.aedes);
            const culex = data.map(d => d.culex);
            const total = data.map(d => d.total);
            
            dailyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [
                        {
                            label: 'Aedes',
                            data: aedes,
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Culex',
                            data: culex,
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Total',
                            data: total,
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        function updateWeeklyChart(data) {
            const ctx = document.getElementById('weeklyChart').getContext('2d');
            
            if (weeklyChart) {
                weeklyChart.destroy();
            }
            
            const weeks = data.map(d => d.week);
            const aedes = data.map(d => d.aedes);
            const culex = data.map(d => d.culex);
            const total = data.map(d => d.total);
            
            weeklyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: weeks,
                    datasets: [
                        {
                            label: 'Aedes',
                            data: aedes,
                            backgroundColor: 'rgba(255, 99, 132, 0.6)'
                        },
                        {
                            label: 'Culex',
                            data: culex,
                            backgroundColor: 'rgba(54, 162, 235, 0.6)'
                        },
                        {
                            label: 'Total',
                            data: total,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        loadData();
        setInterval(loadData, 60000);
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/data')
def api_data():
    from flask import request
    from datetime import datetime, timedelta
    
    days = int(request.args.get('days', 7))
    analyzer = DensityAnalyzer(DB_PATH)
    
    stats = analyzer.get_statistics(days=days)
    weekly_data = analyzer.get_weekly_data(days=days)
    
    daily = []
    aedes_dict = dict(weekly_data['Aedes'])
    culex_dict = dict(weekly_data['Culex'])
    total_dict = dict(weekly_data['Total'])
    
    for date_str in sorted(aedes_dict.keys() | culex_dict.keys() | total_dict.keys()):
        daily.append({
            'date': date_str,
            'aedes': aedes_dict.get(date_str, 0),
            'culex': culex_dict.get(date_str, 0),
            'total': total_dict.get(date_str, 0)
        })
    
    weekly = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    current_date = start_date
    week_num = 1
    
    while current_date < end_date:
        week_start = current_date
        week_end = min(current_date + timedelta(days=7), end_date)
        
        week_aedes = 0
        week_culex = 0
        
        for date_str, count in weekly_data['Aedes']:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if week_start <= date_obj < week_end:
                week_aedes += count
        
        for date_str, count in weekly_data['Culex']:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if week_start <= date_obj < week_end:
                week_culex += count
        
        weekly.append({
            'week': f"Week {week_num}",
            'aedes': week_aedes,
            'culex': week_culex,
            'total': week_aedes + week_culex
        })
        
        current_date = week_end
        week_num += 1
    
    return jsonify({
        'stats': stats,
        'daily': daily,
        'weekly': weekly
    })


if __name__ == '__main__':
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False)
