// ===== Interactive NYC Zone Map (Inline SVG, zero external deps) =====
var MapModule = {
    svg: null,
    circles: [],

    init: function() {
        var container = document.getElementById("map");
        if (!container) return;
        container.innerHTML = "";
        var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("viewBox", "0 0 600 500");
        svg.setAttribute("style", "width:100%;height:400px;border-radius:8px;background:linear-gradient(160deg,#0d2137,#1a3a5c);");
        container.appendChild(svg);
        this.svg = svg;
        this.plotZones();
    },

    _mapX: function(lng) {
        return 50 + (lng + 74.01) / 0.07 * 510;
    },

    _mapY: function(lat) {
        return 40 + (40.79 - lat) / 0.07 * 430;
    },

    getDemandColor: function(level) {
        if (level >= 45) return "#e63946";
        if (level >= 30) return "#ffb703";
        return "#2ec4b6";
    },

    getDemandLevel: function(demand) {
        if (demand >= 45) return "high";
        if (demand >= 30) return "medium";
        return "low";
    },

    getCompetitionBadge: function(comp) {
        var m = { "Low": "badge-low", "Medium": "badge-medium", "High": "badge-high", "Very High": "badge-very-high" };
        return m[comp] || "badge-medium";
    },

    plotZones: function() {
        var self = this;

        var connections = [[237,236],[236,170],[236,162],[162,161],[161,48],[161,90],[161,132],[90,100],[224,237]];
        connections.forEach(function(pair) {
            var a = null, b = null;
            for (var i = 0; i < AppState.zones.length; i++) {
                if (AppState.zones[i].id === pair[0]) a = AppState.zones[i];
                if (AppState.zones[i].id === pair[1]) b = AppState.zones[i];
            }
            if (!a || !b) return;
            var line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", self._mapX(a.lng));
            line.setAttribute("y1", self._mapY(a.lat));
            line.setAttribute("x2", self._mapX(b.lng));
            line.setAttribute("y2", self._mapY(b.lat));
            line.setAttribute("stroke", "rgba(255,255,255,0.08)");
            line.setAttribute("stroke-width", "1");
            line.setAttribute("stroke-dasharray", "4,3");
            self.svg.appendChild(line);
        });

        AppState.zones.forEach(function(zone) {
            var cx = self._mapX(zone.lng);
            var cy = self._mapY(zone.lat);
            var color = self.getDemandColor(zone.demand_avg);
            var radius = zone.demand_avg >= 45 ? 16 : zone.demand_avg >= 30 ? 13 : 10;

            var glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            glow.setAttribute("cx", cx);
            glow.setAttribute("cy", cy);
            glow.setAttribute("r", radius + 4);
            glow.setAttribute("fill", color);
            glow.setAttribute("opacity", "0.15");
            self.svg.appendChild(glow);

            var circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", cx);
            circle.setAttribute("cy", cy);
            circle.setAttribute("r", radius);
            circle.setAttribute("fill", color);
            circle.setAttribute("stroke", "#fff");
            circle.setAttribute("stroke-width", "2");
            circle.setAttribute("opacity", "0.85");
            circle.setAttribute("class", "zone-circle");
            circle.setAttribute("data-zone-id", zone.id);
            circle.style.cursor = "pointer";

            var parts = zone.name.split(" ");
            var abbr = parts[parts.length - 1].substring(0, 6);

            var label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("x", cx);
            label.setAttribute("y", cy + 3);
            label.setAttribute("text-anchor", "middle");
            label.setAttribute("fill", "#fff");
            label.setAttribute("font-size", radius >= 13 ? "9" : "8");
            label.setAttribute("font-weight", "bold");
            label.setAttribute("pointer-events", "none");
            label.textContent = abbr;

            circle.addEventListener("mouseenter", function() {
                circle.setAttribute("stroke-width", "3");
                circle.setAttribute("opacity", "1");
            });

            circle.addEventListener("mouseleave", function() {
                circle.setAttribute("stroke-width", "2");
                circle.setAttribute("opacity", "0.85");
            });

            circle.addEventListener("click", function() {
                self.selectZone(zone);
            });

            self.svg.appendChild(circle);
            self.svg.appendChild(label);
            self.circles.push({ circle: circle, label: label, zone: zone, glow: glow });
        });
    },

    selectZone: function(zone) {
        AppState.selectedZone = zone;
        document.getElementById("selectedZone").textContent = zone.name;
        var detail = document.getElementById("zoneDetail");
        detail.innerHTML =
            "<div><span class='label'>Zone ID</span><span class='value'>" + zone.id + "</span></div>" +
            "<div><span class='label'>Borough</span><span class='value'>" + zone.borough + "</span></div>" +
            "<div><span class='label'>Avg Demand</span><span class='value'>" + zone.demand_avg + "</span></div>" +
            "<div><span class='label'>Avg Supply</span><span class='value'>" + zone.supply_avg + "</span></div>" +
            "<div><span class='label'>Avg Fare</span><span class='value'>$" + zone.avg_fare + "</span></div>" +
            "<div><span class='label'>Pickup Prob</span><span class='value'>" + (zone.pickup_prob * 100).toFixed(0) + "%</span></div>" +
            "<div><span class='label'>Competition</span><span class='badge " + this.getCompetitionBadge(zone.competition) + "'>" + zone.competition + "</span></div>";
        var sel = document.getElementById("simZone");
        if (sel) {
            for (var i = 0; i < sel.options.length; i++) {
                if (parseInt(sel.options[i].value) === zone.id) { sel.value = zone.id; break; }
            }
        }
        ChartsModule.plotForecast(zone);

        this.circles.forEach(function(c) {
            if (c.zone.id === zone.id) {
                c.circle.setAttribute("stroke-width", "4");
                c.circle.setAttribute("stroke", "#00b4d8");
            } else {
                c.circle.setAttribute("stroke-width", "2");
                c.circle.setAttribute("stroke", "#fff");
            }
        });
    }
};
