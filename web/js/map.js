// ===== Interactive NYC Zone Map (Leaflet, inlined no CDN) =====
var MapModule = {
    map: null,
    markers: [],
    init: function() {
        var self = this;
        this.map = L.map("map", {
            center: [40.755, -73.975],
            zoom: 13,
            zoomControl: true,
            attributionControl: false
        });
        // Light tile layer
        L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
            maxZoom: 19,
            maxNativeZoom: 18,
            attribution: "&copy; OSM, &copy; CARTO"
        }).addTo(this.map);
        this.plotZones();
        setTimeout(function() { self.map.invalidateSize(); }, 100);
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
        AppState.zones.forEach(function(zone) {
            var color = self.getDemandColor(zone.demand_avg);
            var radius = zone.demand_avg >= 45 ? 14 : zone.demand_avg >= 30 ? 11 : 8;
            var marker = L.circleMarker([zone.lat, zone.lng], {
                radius: radius,
                fillColor: color,
                color: "#fff",
                weight: 2,
                opacity: 0.9,
                fillOpacity: 0.7
            });
            marker.bindTooltip(zone.name + " (" + zone.demand_avg + ")", { direction: "top" });
            marker.on("click", function() { self.selectZone(zone); });
            marker.addTo(self.map);
            self.markers.push({ marker: marker, zone: zone });
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
        this.map.flyTo([zone.lat, zone.lng], 15, { duration: 0.8 });
    }
};
