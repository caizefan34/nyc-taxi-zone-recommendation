// ===== Decision Simulation Engine =====
var SimulationModule = {
    step: 0,
    isRunning: false,
    selectedPolicy: null,

    run: function() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.step = 0;

        var btn = document.getElementById("runSimBtn");
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px"></span> Running...';

        document.getElementById("applyDecisionBtn").style.display = "none";
        document.getElementById("beforeAfterPanel").style.display = "none";
        document.getElementById("stepProgress").style.display = "flex";
        document.getElementById("stepContent").style.display = "block";

        this.runStep1();
    },

    runStep1: function() {
        var self = this;
        this.step = 1; this.updateProgress();
        document.getElementById("step1Content").classList.add("active");
        document.getElementById("step2Content").classList.remove("active");
        document.getElementById("step3Content").classList.remove("active");
        document.getElementById("step1Loading").style.display = "flex";
        document.getElementById("step1Result").style.display = "none";

        setTimeout(function() {
            document.getElementById("step1Loading").style.display = "none";
            document.getElementById("step1Result").style.display = "block";

            var zone = AppState.selectedZone || AppState.zones[0];
            var hour = parseInt(document.getElementById("simHour")?.value || "10");
            var day = document.getElementById("simDay")?.value || "Monday";
            var month = document.getElementById("simMonth")?.value || "June";

            var dayFactor = {"Monday":0.9,"Tuesday":0.85,"Wednesday":0.82,"Thursday":0.88,"Friday":1.1,"Saturday":1.25,"Sunday":1.05};
            var monthFactor = {"January":0.8,"February":0.78,"March":0.85,"April":0.9,"May":0.95,"June":1.05,"July":1.1,"August":1.08,"September":0.95,"October":0.92,"November":0.88,"December":0.85};
            var hourFactor = Math.sin(hour * Math.PI / 12) * 0.3 + 0.7;
            var peakHour = (hour >= 8 && hour <= 10) || (hour >= 17 && hour <= 19);
            var baseDemand = zone.demand_avg * dayFactor[day] * monthFactor[month] * hourFactor * (peakHour ? 1.15 : 1.0);
            var demandLevel = baseDemand >= 45 ? "very-high" : baseDemand >= 30 ? "high" : baseDemand >= 20 ? "medium" : "low";

            var tbody = document.getElementById("forecastTableBody");
            var html = "";
            var sorted = AppState.zones.slice().sort(function(a,b){return b.demand_avg - a.demand_avg;});
            for (var i = 0; i < Math.min(sorted.length, 15); i++) {
                var z = sorted[i];
                var d = (z.demand_avg * dayFactor[day] * monthFactor[month] * hourFactor * (peakHour ? 1.15 : 1.0)).toFixed(1);
                var s = (z.supply_avg * (peakHour ? 1.1 : 1.0)).toFixed(1);
                var ratio = (parseFloat(d) / parseFloat(s)).toFixed(2);
                var cls = parseFloat(ratio) > 1.0 ? "highlight" : "";
                html += "<tr><td>" + z.id + "</td><td style='text-align:left'>" + z.name + "</td><td>" + z.borough + "</td><td>" + d + "</td><td>" + s + "</td><td class=\"" + cls + "\">" + ratio + "</td></tr>";
            }
            tbody.innerHTML = html;

            document.getElementById("step1Info").textContent =
                zone.name + " @ " + hour + ":00 on " + day + " (" + month + ") → " +
                baseDemand.toFixed(1) + " estimated requests, demand level: " + demandLevel.toUpperCase();

            ChartsModule.plotForecast(zone, hour);
            self.updateProgress();
            setTimeout(function(){self.runStep2(zone, hour, day, month);}, 800);
        }, 900);
    },

    runStep2: function(zone, hour, day, month) {
        var self = this;
        this.step = 2; this.updateProgress();
        document.getElementById("step2Content").classList.add("active");
        document.getElementById("step2Loading").style.display = "flex";
        document.getElementById("step2Result").style.display = "none";

        setTimeout(function() {
            document.getElementById("step2Loading").style.display = "none";
            document.getElementById("step2Result").style.display = "block";

            var candidateZones = [
                {name:"Move to Midtown Center", id:161, strategy:"Two-Step MDP", est_reward:zone.demand_avg * 17 * 0.74, pickup_pct:"78%", risk:"Medium", riskClass:"badge-medium", rank:1},
                {name:"Move to Upper East Side", id:236, strategy:"Two-Step MDP", est_reward:zone.demand_avg * 18 * 0.68, pickup_pct:"68%", risk:"Low", riskClass:"badge-low", rank:2},
                {name:"Move to Chelsea", id:90, strategy:"Single-Step", est_reward:zone.demand_avg * 16 * 0.70, pickup_pct:"70%", risk:"Medium", riskClass:"badge-medium", rank:3},
                {name:"Stay in current zone", id:zone.id, strategy:"Hot Zone", est_reward:zone.demand_avg * 15 * 0.60, pickup_pct:Math.round(zone.pickup_prob*100)+"%", risk:"Low", riskClass:"badge-low", rank:4},
                {name:"Move to Times Square", id:48, strategy:"Single-Step", est_reward:zone.demand_avg * 14 * 0.82, pickup_pct:"82%", risk:"High", riskClass:"badge-high", rank:5}
            ];
            candidateZones.sort(function(a,b){return a.rank - b.rank;});

            var tbody = document.getElementById("policyTableBody");
            var html = "";
            for (var i = 0; i < candidateZones.length; i++) {
                var p = candidateZones[i];
                var cls = p.rank === 1 ? "highlight" : "";
                html += "<tr><td><span class=\"" + p.riskClass + "\">" + p.risk + "</span></td><td style='text-align:left'>" + p.name + "</td><td>" + p.strategy + "</td><td class=\"" + cls + "\">$" + p.est_reward.toFixed(0) + "</td><td>" + p.pickup_pct + "</td></tr>";
            }
            tbody.innerHTML = html;

            self.selectedPolicy = candidateZones[0];
            self.updateProgress();
            setTimeout(function(){self.runStep3(candidateZones[0]);}, 600);
        }, 800);
    },

    runStep3: function(bestPolicy) {
        var self = this;
        this.step = 3; this.updateProgress();
        document.getElementById("step3Content").classList.add("active");
        document.getElementById("step3Loading").style.display = "flex";
        document.getElementById("step3Recommendation").style.display = "none";

        setTimeout(function() {
            document.getElementById("step3Loading").style.display = "none";
            document.getElementById("step3Recommendation").style.display = "block";

            var zone = AppState.selectedZone || AppState.zones[0];
            var confPct = Math.round(70 + Math.random() * 25);
            document.getElementById("recZone").textContent = bestPolicy.name;
            document.getElementById("recExpectedReward").textContent = "$" + bestPolicy.est_reward.toFixed(0);
            document.getElementById("recUtilization").textContent = bestPolicy.pickup_pct;
            document.getElementById("recConfidence").textContent = confPct + "%";
            document.getElementById("recStrategy").textContent = bestPolicy.strategy;

            document.getElementById("recStrategyBadge").textContent = bestPolicy.strategy + " Policy";
            document.getElementById("recStrategyBadge").style.background = getComputedStyle(document.documentElement).getPropertyValue('--accent');

            document.getElementById("applyDecisionBtn").style.display = "inline-flex";
            self.isRunning = false;
            var btn = document.getElementById("runSimBtn");
            btn.disabled = false;
            btn.innerHTML = '&#9654; Run AI Decision';
        }, 700);
    },

    applyDecision: function() {
        document.getElementById("beforeAfterPanel").style.display = "block";
        var zone = AppState.selectedZone || AppState.zones[0];

        var beforeRevenue = (zone.demand_avg * zone.avg_fare * 0.45).toFixed(0);
        var beforeUtil = Math.round(zone.pickup_prob * 100);
        var beforeWait = (Math.random() * 3 + 2).toFixed(1);
        var afterRevenue = (parseFloat(beforeRevenue) * 1.18).toFixed(0);
        var afterUtil = Math.min(100, beforeUtil + 12);
        var afterWait = (Math.random() * 1.5 + 1).toFixed(1);

        document.getElementById("beforeRevenue").textContent = "$" + beforeRevenue;
        document.getElementById("beforeUtilization").textContent = beforeUtil + "%";
        document.getElementById("beforeWait").textContent = beforeWait + " min";
        document.getElementById("afterRevenue").textContent = "$" + afterRevenue;
        document.getElementById("afterUtilization").textContent = afterUtil + "%";
        document.getElementById("afterWait").textContent = afterWait + " min";

        var revImp = Math.round((parseFloat(afterRevenue) - parseFloat(beforeRevenue)) / parseFloat(beforeRevenue) * 100);
        var utilImp = afterUtil - beforeUtil;
        var waitImp = Math.round((parseFloat(beforeWait) - parseFloat(afterWait)) / parseFloat(beforeWait) * 100);

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