// ===== Decision Simulation Engine =====
var SimulationModule = {
    step: 0,
    isRunning: false,

    run: function() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.step = 0;

        var btn = document.getElementById("runSimBtn");
        btn.disabled = true;
        btn.innerHTML = "Running...";

        document.getElementById("applyDecisionBtn").style.display = "none";
        document.getElementById("beforeAfterPanel").style.display = "none";
        document.getElementById("stepProgress").style.display = "flex";
        document.getElementById("stepContent").style.display = "block";

        this.runStep1();
    },

    runStep1: function() {
        this.step = 1;
        this.updateProgress();
        document.getElementById("step1Content").classList.add("active");
        document.getElementById("step2Content").classList.remove("active");
        document.getElementById("step3Content").classList.remove("active");

        document.getElementById("step1Loading").style.display = "flex";
        document.getElementById("step1Result").style.display = "none";

        var self = this;
        setTimeout(function() {
            document.getElementById("step1Loading").style.display = "none";
            document.getElementById("step1Result").style.display = "block";

            var zone = AppState.selectedZone || AppState.zones[0];
            var hour = parseInt(document.getElementById("simHour")?.value || "10");
            var day = document.getElementById("simDay")?.value || "Monday";
            var month = document.getElementById("simMonth")?.value || "June";

            var dayFactor = { "Monday": 0.9, "Tuesday": 0.85, "Wednesday": 0.82, "Thursday": 0.88, "Friday": 1.1, "Saturday": 1.25, "Sunday": 1.05 };
            var monthFactor = { "January": 0.8, "February": 0.78, "March": 0.85, "April": 0.9, "May": 0.95, "June": 1.05, "July": 1.1, "August": 1.08, "September": 0.95, "October": 0.92, "November": 0.88, "December": 0.85 };
            var hourFactor = Math.sin(hour * Math.PI / 12) * 0.3 + 0.7;

            var baseDemand = zone.demand_avg * dayFactor[day] * monthFactor[month] * hourFactor;
            var peakHour = (hour >= 8 && hour <= 10) || (hour >= 17 && hour <= 19);
            if (peakHour) baseDemand *= 1.15;

            var tbody = document.getElementById("forecastTableBody");
            var html = "";
            var sorted = AppState.zones.slice().sort(function(a, b) { return b.demand_avg - a.demand_avg; });
            for (var i = 0; i < sorted.length; i++) {
                var z = sorted[i];
                var d = (z.demand_avg * dayFactor[day] * monthFactor[month] * hourFactor).toFixed(1);
                var s = (z.supply_avg * (peakHour ? 1.1 : 1.0)).toFixed(1);
                var ratio = (parseFloat(d) / parseFloat(s)).toFixed(2);
                var cls = parseFloat(ratio) > 1.0 ? "highlight" : "";
                html += "<tr><td>" + z.name + "</td><td>" + d + "</td><td>" + s + "</td><td class=\"" + cls + "\">" + ratio + "</td></tr>";
            }
            tbody.innerHTML = html;

            document.getElementById("step1Info").textContent = "Predicted demand for " + zone.name + " at hour " + hour + " on " + day + " (" + month + "): " + baseDemand.toFixed(1) + " estimated requests";

            self.step = 2;
            self.updateProgress();
            setTimeout(function() { self.runStep2(); }, 600);
        }, 1200);
    },

    runStep2: function() {
        document.getElementById("step2Content").classList.add("active");
        document.getElementById("step2Loading").style.display = "flex";
        document.getElementById("step2Result").style.display = "none";

        var self = this;
        setTimeout(function() {
            document.getElementById("step2Loading").style.display = "none";
            document.getElementById("step2Result").style.display = "block";

            var zone = AppState.selectedZone || AppState.zones[0];
            var policies = [
                { name: "Stay in Zone", reward: (zone.demand_avg * 15 * 0.6).toFixed(0), util: (zone.pickup_prob * 100).toFixed(0) + "%", risk: "Low" },
                { name: "Move to Midtown", reward: (zone.demand_avg * 17 * 0.72).toFixed(0), util: "78%", risk: "Medium" },
                { name: "Move to Times Square", reward: (zone.demand_avg * 14 * 0.82).toFixed(0), util: "82%", risk: "High" },
                { name: "Move to Chelsea", reward: (zone.demand_avg * 16 * 0.68).toFixed(0), util: "70%", risk: "Medium" },
                { name: "Move to Upper West Side", reward: (zone.demand_avg * 16 * 0.65).toFixed(0), util: "65%", risk: "Low" }
            ];

            var tbody = document.getElementById("policyTableBody");
            var html = "";
            var riskClass = { "Low": "badge-low", "Medium": "badge-medium", "High": "badge-high" };
            for (var i = 0; i < policies.length; i++) {
                var p = policies[i];
                var cls = (i === 0) ? "highlight" : "";
                html += "<tr><td><span class=\"badge " + riskClass[p.risk] + "\">" + p.risk + "</span></td><td>" + p.name + "</td><td class=\"" + cls + "\">$" + p.reward + "</td><td>" + p.util + "</td></tr>";
            }
            tbody.innerHTML = html;

            self.step = 3;
            self.updateProgress();
            setTimeout(function() { self.runStep3(); }, 600);
        }, 1000);
    },

    runStep3: function() {
        document.getElementById("step3Content").classList.add("active");
        document.getElementById("step3Loading").style.display = "flex";
        document.getElementById("step3Recommendation").style.display = "none";

        var self = this;
        setTimeout(function() {
            document.getElementById("step3Loading").style.display = "none";
            document.getElementById("step3Recommendation").style.display = "block";

            var zone = AppState.selectedZone || AppState.zones[0];
            var reward = (zone.demand_avg * 17 * 0.72).toFixed(0);

            document.getElementById("recZone").textContent = "Move to Midtown Center";
            document.getElementById("recExpectedReward").textContent = "$" + reward;
            document.getElementById("recUtilization").textContent = "78%";
            document.getElementById("recConfidence").textContent = "Medium-High";

            document.getElementById("applyDecisionBtn").style.display = "block";

            self.isRunning = false;
            var btn = document.getElementById("runSimBtn");
            btn.disabled = false;
            btn.innerHTML = "Run AI Decision";
        }, 1000);
    },

    applyDecision: function() {
        document.getElementById("beforeAfterPanel").style.display = "block";
        var zone = AppState.selectedZone || AppState.zones[0];

        var beforeRevenue = (zone.demand_avg * zone.avg_fare * 0.45).toFixed(0);
        var beforeUtil = (zone.pickup_prob * 100).toFixed(0);
        var beforeWait = (Math.random() * 3 + 2).toFixed(1);

        var afterRevenue = (parseFloat(beforeRevenue) * 1.18).toFixed(0);
        var afterUtil = Math.min(100, parseFloat(beforeUtil) + 12).toFixed(0);
        var afterWait = (Math.random() * 1.5 + 1).toFixed(1);

        document.getElementById("beforeRevenue").textContent = "$" + beforeRevenue;
        document.getElementById("beforeUtilization").textContent = beforeUtil + "%";
        document.getElementById("beforeWait").textContent = beforeWait + " min";

        document.getElementById("afterRevenue").textContent = "$" + afterRevenue;
        document.getElementById("afterUtilization").textContent = afterUtil + "%";
        document.getElementById("afterWait").textContent = afterWait + " min";

        var revImp = ((parseFloat(afterRevenue) - parseFloat(beforeRevenue)) / parseFloat(beforeRevenue) * 100).toFixed(0);
        var utilImp = (parseFloat(afterUtil) - parseFloat(beforeUtil)).toFixed(0);
        var waitImp = ((parseFloat(beforeWait) - parseFloat(afterWait)) / parseFloat(beforeWait) * 100).toFixed(0);

        document.getElementById("improvementRevenue").textContent = "+" + revImp + "%";
        document.getElementById("improvementUtilization").textContent = "+" + utilImp + "%";
        document.getElementById("improvementWait").textContent = "-" + waitImp + "%";

        ChartsModule.plotBeforeAfter(zone, parseFloat(beforeRevenue), parseFloat(afterRevenue));
    },

    updateProgress: function() {
        var dots = document.querySelectorAll(".step-dot");
        for (var i = 0; i < dots.length; i++) {
            dots[i].className = "step-dot";
            if (i + 1 < this.step) dots[i].classList.add("done");
            else if (i + 1 === this.step) dots[i].classList.add("active");
        }
    }
};