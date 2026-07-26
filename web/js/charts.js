// ===== Lightweight Charts (no dependencies) =====
var ChartsModule = {
    plotForecast: function(zone) {
        var div = document.getElementById("forecastChart");
        if (!div) return;
        var w = div.clientWidth || 500, h = 280;
        var hourlyData = [];
        for (var hh = 0; hh < 24; hh++) {
            var hf = Math.sin(hh * Math.PI / 12) * 0.3 + 0.7;
            if ((hh >= 8 && hh <= 10) || (hh >= 17 && hh <= 19)) hf *= 1.15;
            hourlyData.push({
                hour: hh + ":00",
                historical: parseFloat((zone.demand_avg * (Math.sin(hh * Math.PI / 12) * 0.25 + 0.75)).toFixed(1)),
                forecast: parseFloat((zone.demand_avg * hf).toFixed(1))
            });
        }
        var maxVal = Math.max.apply(null, hourlyData.map(function(d){ return Math.max(d.historical, d.forecast); })) * 1.15;
        var pad = {t: 30, r: 20, b: 40, l: 50};
        var cw = w - pad.l - pad.r, ch = h - pad.t - pad.b;
        var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
        svg += '<text x="' + (w/2) + '" y="18" text-anchor="middle" fill="#ccc" font-size="13" font-weight="bold">' + zone.name + ' — Hourly Demand</text>';
        // Y axis grid
        for (var g = 0; g <= 4; g++) {
            var yv = maxVal * g / 4;
            var yy = pad.t + ch - (g / 4 * ch);
            svg += '<line x1="' + pad.l + '" y1="' + yy + '" x2="' + (w - pad.r) + '" y2="' + yy + '" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>';
            svg += '<text x="' + (pad.l - 5) + '" y="' + (yy + 4) + '" text-anchor="end" fill="#667" font-size="10">' + yv.toFixed(0) + '</text>';
        }
        // Plot lines
        var histPts = [], forePts = [];
        for (var i = 0; i < hourlyData.length; i++) {
            var x = pad.l + (i / (hourlyData.length - 1)) * cw;
            var yh = pad.t + ch - (hourlyData[i].historical / maxVal) * ch;
            var yf = pad.t + ch - (hourlyData[i].forecast / maxVal) * ch;
            histPts.push(x + ',' + yh);
            forePts.push(x + ',' + yf);
        }
        svg += '<polyline points="' + histPts.join(' ') + '" fill="none" stroke="#667" stroke-width="2" stroke-dasharray="5,3" opacity="0.7"/>';
        svg += '<polyline points="' + forePts.join(' ') + '" fill="none" stroke="#00b4d8" stroke-width="2.5"/>';
        // X labels (every 3 hours)
        for (var i2 = 0; i2 < hourlyData.length; i2 += 3) {
            var xl = pad.l + (i2 / (hourlyData.length - 1)) * cw;
            svg += '<text x="' + xl + '" y="' + (h - 8) + '" text-anchor="middle" fill="#667" font-size="9">' + hourlyData[i2].hour + '</text>';
        }
        // Legend
        svg += '<line x1="' + (w/2 - 80) + '" y1="' + (h - 22) + '" x2="' + (w/2 - 50) + '" y2="' + (h - 22) + '" stroke="#667" stroke-width="2" stroke-dasharray="5,3"/>';
        svg += '<text x="' + (w/2 - 45) + '" y="' + (h - 18) + '" fill="#667" font-size="10">Historical</text>';
        svg += '<line x1="' + (w/2 + 10) + '" y1="' + (h - 22) + '" x2="' + (w/2 + 40) + '" y2="' + (h - 22) + '" stroke="#00b4d8" stroke-width="2"/>';
        svg += '<text x="' + (w/2 + 45) + '" y="' + (h - 18) + '" fill="#00b4d8" font-size="10">Forecast</text>';
        svg += '</svg>';
        div.innerHTML = svg;
    },

    plotPolicyComparison: function() {
        var div = document.getElementById("policyChart");
        if (!div) return;
        var w = div.clientWidth || 500, h = 280;
        var items = [
            {label:"Stay", r:920, v:850, u:45},
            {label:"Random", r:1050, v:980, u:52},
            {label:"Hot Zone", r:1689, v:1450, u:68},
            {label:"Single-Step", r:1768, v:1520, u:72},
            {label:"AI(DQN)", r:1822, v:1600, u:78}
        ];
        var maxR = 2000, pad = {t: 30, r: 20, b: 50, l: 60};
        var cw = w - pad.l - pad.r, barW = Math.min(50, (cw / items.length) * 0.25);
        var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
        svg += '<text x="' + (w/2) + '" y="18" text-anchor="middle" fill="#ccc" font-size="13" font-weight="bold">Policy Performance</text>';
        for (var g = 0; g <= 4; g++) {
            var yy = pad.t + (h - pad.t - pad.b) * (1 - g/4);
            svg += '<line x1="' + pad.l + '" y1="' + yy + '" x2="' + (w - pad.r) + '" y2="' + yy + '" stroke="rgba(255,255,255,0.06)"/>';
            svg += '<text x="' + (pad.l - 5) + '" y="' + (yy + 4) + '" text-anchor="end" fill="#667" font-size="9">$' + (maxR * g / 4) + '</text>';
        }
        for (var i = 0; i < items.length; i++) {
            var xc = pad.l + (i + 0.5) * (cw / items.length);
            var hR = (items[i].r / maxR) * (h - pad.t - pad.b);
            var hV = (items[i].v / maxR) * (h - pad.t - pad.b);
            svg += '<rect x="' + (xc - barW - 2) + '" y="' + (h - pad.b - hR) + '" width="' + barW + '" height="' + hR + '" fill="#00b4d8" rx="3"/>';
            svg += '<rect x="' + (xc + 2) + '" y="' + (h - pad.b - hV) + '" width="' + barW + '" height="' + hV + '" fill="#2ec4b6" rx="3"/>';
            svg += '<text x="' + xc + '" y="' + (h - 5) + '" text-anchor="middle" fill="#889" font-size="9" transform="rotate(-30,' + xc + ',' + (h - 5) + ')">' + items[i].label + '</text>';
        }
        svg += '<rect x="' + (w/2 - 70) + '" y="8" width="10" height="10" fill="#00b4d8" rx="2"/>';
        svg += '<text x="' + (w/2 - 55) + '" y="17" fill="#889" font-size="9">Reward</text>';
        svg += '<rect x="' + (w/2 - 10) + '" y="8" width="10" height="10" fill="#2ec4b6" rx="2"/>';
        svg += '<text x="' + (w/2 + 5) + '" y="17" fill="#889" font-size="9">Revenue</text>';
        svg += '</svg>';
        div.innerHTML = svg;
    },

    plotBeforeAfter: function(zone, beforeRev, afterRev) {
        var div = document.getElementById("beforeAfterChart");
        if (!div) return;
        var w = div.clientWidth || 500, h = 200;
        var labels = ["Revenue", "Utilization", "Wait Time"];
        var before = [beforeRev, (zone.pickup_prob * 100).toFixed(0), 4.5];
        var after = [afterRev, Math.min(100, (zone.pickup_prob * 100 + 12)).toFixed(0), 2.0];
        var maxVals = [Math.max(before[0], after[0]) * 1.3, 100, 6];
        var pad = {t: 25, r: 10, b: 30, l: 10}, barW = 30;
        var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
        svg += '<text x="' + (w/2) + '" y="16" text-anchor="middle" fill="#ccc" font-size="12" font-weight="bold">Decision Impact: Before vs After</text>';
        for (var i = 0; i < 3; i++) {
            var cx = pad.l + (i + 0.5) * ((w - pad.l - pad.r) / 3);
            var ch = h - pad.t - pad.b;
            var bh = (before[i] / maxVals[i]) * ch;
            var ah = (after[i] / maxVals[i]) * ch;
            svg += '<rect x="' + (cx - barW - 3) + '" y="' + (h - pad.b - bh) + '" width="' + barW + '" height="' + bh + '" fill="#4a5568" rx="3"/>';
            svg += '<rect x="' + (cx + 3) + '" y="' + (h - pad.b - ah) + '" width="' + barW + '" height="' + ah + '" fill="#2ec4b6" rx="3"/>';
            svg += '<text x="' + cx + '" y="' + (h - 5) + '" text-anchor="middle" fill="#889" font-size="10">' + labels[i] + '</text>';
            svg += '<text x="' + (cx - barW/2 - 3) + '" y="' + (h - pad.b - bh - 5) + '" text-anchor="middle" fill="#889" font-size="9">' + before[i] + '</text>';
            svg += '<text x="' + (cx + barW/2 + 3) + '" y="' + (h - pad.b - ah - 5) + '" text-anchor="middle" fill="#2ec4b6" font-size="9">' + after[i] + '</text>';
        }
        svg += '<rect x="' + (w/2 - 60) + '" y="6" width="8" height="8" fill="#4a5568" rx="2"/>';
        svg += '<text x="' + (w/2 - 48) + '" y="14" fill="#889" font-size="9">Before</text>';
        svg += '<rect x="' + (w/2 - 10) + '" y="6" width="8" height="8" fill="#2ec4b6" rx="2"/>';
        svg += '<text x="' + (w/2 + 2) + '" y="14" fill="#2ec4b6" font-size="9">After</text>';
        svg += '</svg>';
        div.innerHTML = svg;
    },

    init: function() {
        this.plotPolicyComparison();
    }
};