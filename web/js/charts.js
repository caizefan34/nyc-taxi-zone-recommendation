// ===== Lightweight SVG Charts (no dependencies) =====
var ChartsModule = {
    plotForecast: function(zone, highlightHour) {
        var div = document.getElementById("forecastChart");
        if (!div) return;
        var w = Math.max(div.clientWidth || 500, 400), h = 300;
        var hourlyData = [];
        for (var hh = 0; hh < 24; hh++) {
            var hf = Math.sin(hh * Math.PI / 12) * 0.3 + 0.7;
            if ((hh >= 8 && hh <= 10) || (hh >= 17 && hh <= 19)) hf *= 1.15;
            hourlyData.push({
                hour: hh,
                label: hh + ":00",
                historical: parseFloat((zone.demand_avg * (Math.sin(hh * Math.PI / 12) * 0.25 + 0.75)).toFixed(1)),
                forecast: parseFloat((zone.demand_avg * hf).toFixed(1))
            });
        }
        var maxVal = Math.max.apply(null, hourlyData.map(function(d){return Math.max(d.historical,d.forecast);})) * 1.2;
        var pad = {t:35, r:25, b:45, l:55};
        var cw = w - pad.l - pad.r, ch = h - pad.t - pad.b;
        var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
        // Title
        svg += '<text x="' + (w/2) + '" y="20" text-anchor="middle" fill="#e0e6ed" font-size="14" font-weight="700" font-family="system-ui,sans-serif">Hourly Demand Forecast — ' + zone.name + '</text>';
        // Gridlines
        for (var g = 0; g <= 4; g++) {
            var yv = maxVal * g / 4, yy = pad.t + ch - (g / 4 * ch);
            svg += '<line x1="' + pad.l + '" y1="' + yy + '" x2="' + (w - pad.r) + '" y2="' + yy + '" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>';
            svg += '<text x="' + (pad.l - 6) + '" y="' + (yy + 4) + '" text-anchor="end" fill="#667" font-size="10" font-family="monospace">' + yv.toFixed(0) + '</text>';
        }
        // Peak shading
        svg += '<rect x="' + (pad.l + (8/24)*cw) + '" y="' + pad.t + '" width="' + ((10-8)/24*cw) + '" height="' + ch + '" fill="rgba(255,183,3,0.03)" rx="2"/>';
        svg += '<rect x="' + (pad.l + (12/24)*cw) + '" y="' + pad.t + '" width="' + ((10-8)/24*cw) + '" height="' + ch + '" fill="rgba(255,183,3,0.03)" rx="2"/>';
        svg += '<rect x="' + (pad.l + (17/24)*cw) + '" y="' + pad.t + '" width="' + ((19-17)/24*cw) + '" height="' + ch + '" fill="rgba(255,183,3,0.03)" rx="2"/>';
        // Highlight hour
        if (highlightHour !== undefined) {
            var hx = pad.l + (highlightHour / 23) * cw;
            svg += '<line x1="' + hx + '" y1="' + pad.t + '" x2="' + hx + '" y2="' + (pad.t+ch) + '" stroke="rgba(0,180,216,0.3)" stroke-width="2" stroke-dasharray="4,4"/>';
        }
        // Polygons
        var hPts = [], fPts = [], hArea = [], fArea = [];
        for (var i = 0; i < hourlyData.length; i++) {
            var x = pad.l + (i / (hourlyData.length - 1)) * cw;
            var yh = pad.t + ch - (hourlyData[i].historical / maxVal) * ch;
            var yf = pad.t + ch - (hourlyData[i].forecast / maxVal) * ch;
            hPts.push(x + ',' + yh); fPts.push(x + ',' + yf);
        }
        // Area fills
        hArea.push(pad.l + ',' + (pad.t+ch)); hArea = hArea.concat(hPts); hArea.push((w-pad.r) + ',' + (pad.t+ch));
        svg += '<polygon points="' + hArea.join(' ') + '" fill="rgba(136,136,170,0.06)"/>';
        var fAreaPts = [pad.l + ',' + (pad.t+ch)].concat(fPts).concat([(w-pad.r) + ',' + (pad.t+ch)]);
        svg += '<polygon points="' + fAreaPts.join(' ') + '" fill="rgba(0,180,216,0.06)"/>';
        // Lines
        svg += '<polyline points="' + hPts.join(' ') + '" fill="none" stroke="#555" stroke-width="2" stroke-dasharray="6,3" opacity="0.6"/>';
        svg += '<polyline points="' + fPts.join(' ') + '" fill="none" stroke="#00b4d8" stroke-width="2.5"/>';
        // X labels (every 3h)
        for (var i2 = 0; i2 < 24; i2 += 3) {
            var xl = pad.l + (i2 / 23) * cw;
            var isHighlight = highlightHour !== undefined && i2 === Math.floor(highlightHour/3)*3;
            svg += '<text x="' + xl + '" y="' + (h - 10) + '" text-anchor="middle" fill="' + (isHighlight ? '#00b4d8' : '#667') + '" font-size="10" font-family="monospace" font-weight="' + (isHighlight ? 'bold' : 'normal') + '">' + hourlyData[i2].label + '</text>';
        }
        // Legend
        var lx = w/2 - 95, ly = h - 28;
        svg += '<line x1="' + lx + '" y1="' + ly + '" x2="' + (lx+25) + '" y2="' + ly + '" stroke="#555" stroke-width="2" stroke-dasharray="6,3"/>';
        svg += '<text x="' + (lx+30) + '" y="' + (ly+4) + '" fill="#889" font-size="10">Historical avg</text>';
        svg += '<line x1="' + (lx+120) + '" y1="' + ly + '" x2="' + (lx+145) + '" y2="' + ly + '" stroke="#00b4d8" stroke-width="2.5"/>';
        svg += '<text x="' + (lx+150) + '" y="' + (ly+4) + '" fill="#00b4d8" font-size="10">AI Forecast</text>';
        svg += '</svg>';
        div.innerHTML = svg;
    },

    plotPolicyComparison: function() {
        var div = document.getElementById("policyChart");
        if (!div) return;
        var w = Math.max(div.clientWidth || 500, 400), h = 300;
        var items = [
            {label:"Stay", color:"#4a5568", r:920, v:850},
            {label:"Random", color:"#667799", r:1050, v:980},
            {label:"Hot Zone", color:"#ffb703", r:1689, v:1450},
            {label:"Step MDP", color:"#00b4d8", r:1768, v:1520},
            {label:"Two-Step", color:"#2ec4b6", r:1850, v:1620},
            {label:"DQN (AI)", color:"#7c5ce7", r:1822, v:1600}
        ];
        var maxR = 2100, pad = {t:35, r:25, b:55, l:60};
        var cw = w - pad.l - pad.r;
        var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
        svg += '<text x="' + (w/2) + '" y="20" text-anchor="middle" fill="#e0e6ed" font-size="14" font-weight="700">Policy Revenue Comparison (50-driver benchmark)</text>';
        for (var g = 0; g <= 4; g++) {
            var yy = pad.t + (h - pad.t - pad.b) * (1 - g/4);
            svg += '<line x1="'+pad.l+'" y1="'+yy+'" x2="'+(w-pad.r)+'" y2="'+yy+'" stroke="rgba(255,255,255,0.05)"/>';
            svg += '<text x="'+(pad.l-6)+'" y="'+(yy+4)+'" text-anchor="end" fill="#667" font-size="10" font-family="monospace">$'+Math.round(maxR*g/4)+'</text>';
        }
        var n = items.length, barW = Math.min(45, (cw/n)*0.55), gap = cw/n;
        for (var i = 0; i < n; i++) {
            var xc = pad.l + (i + 0.5) * gap;
            var hR = (items[i].r / maxR) * (h - pad.t - pad.b);
            var hV = (items[i].v / maxR) * (h - pad.t - pad.b);
            svg += '<rect x="'+(xc-barW/2-2)+'" y="'+(h-pad.b-hR)+'" width="'+(barW/2)+'" height="'+hR+'" fill="'+items[i].color+'" rx="3" opacity="0.85"/>';
            svg += '<rect x="'+(xc+2)+'" y="'+(h-pad.b-hV)+'" width="'+(barW/2)+'" height="'+hV+'" fill="'+items[i].color+'" rx="3" opacity="0.45"/>';
            svg += '<text x="'+xc+'" y="'+(h-35)+'" text-anchor="middle" fill="#889" font-size="9" transform="rotate(-35,'+xc+','+(h-35)+')">'+items[i].label+'</text>';
            svg += '<text x="'+xc+'" y="'+(h-pad.b-hR-4)+'" text-anchor="middle" fill="'+items[i].color+'" font-size="9" font-weight="600">$'+items[i].r+'</text>';
        }
        var lx = w/2 - 80, ly = h - 18;
        svg += '<rect x="'+lx+'" y="'+(ly-8)+'" width="10" height="10" fill="rgba(255,255,255,0.85)" rx="2"/>';
        svg += '<text x="'+(lx+14)+'" y="'+ly+'" fill="#889" font-size="10">Reward</text>';
        svg += '<rect x="'+(lx+65)+'" y="'+(ly-8)+'" width="10" height="10" fill="rgba(255,255,255,0.45)" rx="2"/>';
        svg += '<text x="'+(lx+79)+'" y="'+ly+'" fill="#889" font-size="10">Revenue</text>';
        svg += '</svg>';
        div.innerHTML = svg;
    },

    plotBeforeAfter: function(zone, beforeRev, afterRev) {
        var div = document.getElementById("beforeAfterChart");
        if (!div) return;
        var w = Math.max(div.clientWidth || 500, 400), h = 240;
        var labels = ["Revenue ($)", "Utilization (%)", "Wait (min)"];
        var before = [beforeRev, Math.round(zone.pickup_prob * 100), 4.2];
        var after = [afterRev, Math.min(100, Math.round(zone.pickup_prob * 100 + 12)), 2.0];
        var maxVals = [Math.max(before[0], after[0]) * 1.3, 105, 6.5];
        var pad = {t:30, r:10, b:35, l:10}, barW = 28;
        var svg = '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
        svg += '<text x="'+(w/2)+'" y="18" text-anchor="middle" fill="#e0e6ed" font-size="14" font-weight="700">Before vs After AI Recommendation</text>';
        for (var i = 0; i < 3; i++) {
            var cx = pad.l + (i + 0.5) * ((w - pad.l - pad.r) / 3);
            var ch2 = h - pad.t - pad.b;
            var bh = (before[i] / maxVals[i]) * ch2;
            var ah = (after[i] / maxVals[i]) * ch2;
            svg += '<rect x="'+(cx-barW-2)+'" y="'+(h-pad.b-bh)+'" width="'+barW+'" height="'+bh+'" fill="#4a5568" rx="4"/>';
            svg += '<rect x="'+(cx+2)+'" y="'+(h-pad.b-ah)+'" width="'+barW+'" height="'+ah+'" fill="#2ec4b6" rx="4"/>';
            svg += '<text x="'+cx+'" y="'+(h-8)+'" text-anchor="middle" fill="#889" font-size="10">'+labels[i]+'</text>';
            svg += '<text x="'+(cx-barW/2-2)+'" y="'+(h-pad.b-bh-5)+'" text-anchor="middle" fill="#889" font-size="9" font-weight="600">'+before[i]+'</text>';
            svg += '<text x="'+(cx+barW/2+2)+'" y="'+(h-pad.b-ah-5)+'" text-anchor="middle" fill="#2ec4b6" font-size="9" font-weight="600">'+after[i]+'</text>';
        }
        var lx = w/2 - 60, ly = 16;
        svg += '<rect x="'+lx+'" y="'+(ly-7)+'" width="8" height="8" fill="#4a5568" rx="2"/>';
        svg += '<text x="'+(lx+12)+'" y="'+ly+'" fill="#889" font-size="9">Before</text>';
        svg += '<rect x="'+(lx+52)+'" y="'+(ly-7)+'" width="8" height="8" fill="#2ec4b6" rx="2"/>';
        svg += '<text x="'+(lx+64)+'" y="'+ly+'" fill="#2ec4b6" font-size="9">After</text>';
        svg += '</svg>';
        div.innerHTML = svg;
    },

    init: function() {
        this.plotPolicyComparison();
    }
};