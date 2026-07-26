// ===== Interactive Charts =====
var ChartsModule = {

    plotForecast: function(zone) {
        var hourlyData = [];
        for (var h = 0; h < 24; h++) {
            var hourFactor = Math.sin(h * Math.PI / 12) * 0.3 + 0.7;
            if ((h >= 8 && h <= 10) || (h >= 17 && h <= 19)) hourFactor *= 1.15;
            hourlyData.push({
                hour: h,
                historical: parseFloat((zone.demand_avg * (Math.sin(h * Math.PI / 12) * 0.25 + 0.75)).toFixed(1)),
                forecast: parseFloat((zone.demand_avg * hourFactor).toFixed(1))
            });
        }

        var historical = hourlyData.map(function(d) { return d.historical; });
        var forecast = hourlyData.map(function(d) { return d.forecast; });
        var hours = hourlyData.map(function(d) { return d.hour + ":00"; });

        var forecastDiv = document.getElementById("forecastChart");
        if (!forecastDiv) return;

        var trace1 = {
            x: hours, y: historical,
            type: "scatter", mode: "lines+markers",
            name: "Historical Avg",
            line: { color: "#8899aa", width: 2, dash: "dot" },
            marker: { size: 4 }
        };
        var trace2 = {
            x: hours, y: forecast,
            type: "scatter", mode: "lines+markers",
            name: "Forecast",
            line: { color: "#00b4d8", width: 3 },
            marker: { size: 5 }
        };
        var layout = {
            title: { text: zone.name + " — Hourly Demand Forecast", font: { color: "#fff", size: 14 } },
            paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#8899aa", size: 11 },
            xaxis: { title: "Hour", gridcolor: "rgba(255,255,255,0.05)", tickangle: -45 },
            yaxis: { title: "Demand (trips)", gridcolor: "rgba(255,255,255,0.05)" },
            margin: { l: 50, r: 20, t: 40, b: 60 },
            legend: { font: { color: "#8899aa", size: 10 }, orientation: "h", y: -0.2 },
            hovermode: "x unified"
        };
        Plotly.newPlot(forecastDiv, [trace1, trace2], layout, { responsive: true, displayModeBar: false });
    },

    plotPolicyComparison: function() {
        var div = document.getElementById("policyChart");
        if (!div) return;

        var policies = ["Stay", "Random", "Hot Zone", "Single-Step", "AI Policy (DQN)"];
        var reward = [920, 1050, 1689, 1768, 1822];
        var revenue = [850, 980, 1450, 1520, 1600];
        var utilization = [45, 52, 68, 72, 78];

        var trace1 = { x: policies, y: reward, type: "bar", name: "Avg Daily Reward", marker: { color: "#00b4d8" } };
        var trace2 = { x: policies, y: revenue, type: "bar", name: "Revenue ($)", marker: { color: "#2ec4b6" } };
        var trace3 = { x: policies, y: utilization, type: "scatter", mode: "lines+markers", name: "Utilization %", yaxis: "y2", line: { color: "#ffb703", width: 3 }, marker: { size: 8 } };

        var layout = {
            title: { text: "Policy Performance Comparison", font: { color: "#fff", size: 14 } },
            paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#8899aa", size: 11 },
            xaxis: { title: "Policy", gridcolor: "rgba(255,255,255,0.05)" },
            yaxis: { title: "Reward / Revenue ($)", gridcolor: "rgba(255,255,255,0.05)" },
            yaxis2: { title: "Utilization %", overlaying: "y", side: "right", range: [0, 100], gridcolor: "rgba(255,255,255,0.02)" },
            margin: { l: 60, r: 60, t: 40, b: 60 },
            legend: { font: { color: "#8899aa", size: 10 }, orientation: "h", y: -0.2 },
            barmode: "group",
            hovermode: "x unified"
        };
        Plotly.newPlot(div, [trace1, trace2, trace3], layout, { responsive: true, displayModeBar: false });
    },

    plotBeforeAfter: function(zone, beforeRev, afterRev) {
        var div = document.getElementById("beforeAfterChart");
        if (!div) return;

        var trace1 = {
            x: ["Revenue", "Utilization", "Wait Time"], y: [beforeRev, (zone.pickup_prob * 100).toFixed(0), 4.5],
            type: "bar", name: "Before",
            marker: { color: "#4a5568" }
        };
        var trace2 = {
            x: ["Revenue", "Utilization", "Wait Time"], y: [afterRev, Math.min(100, (zone.pickup_prob * 100 + 12)).toFixed(0), 2.0],
            type: "bar", name: "After",
            marker: { color: "#2ec4b6" }
        };

        var layout = {
            title: { text: "Before vs After: Decision Impact", font: { color: "#fff", size: 14 } },
            paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#8899aa", size: 11 },
            xaxis: { gridcolor: "rgba(255,255,255,0.05)" },
            yaxis: { title: "Value", gridcolor: "rgba(255,255,255,0.05)" },
            margin: { l: 50, r: 20, t: 40, b: 50 },
            legend: { font: { color: "#8899aa", size: 10 }, orientation: "h", y: -0.2 },
            barmode: "group",
            hovermode: "x unified"
        };
        Plotly.newPlot(div, [trace1, trace2], layout, { responsive: true, displayModeBar: false });
    },

    init: function() {
        this.plotPolicyComparison();
    }
};