// Formato del tooltip del umbral en «Predecir»: 0.52 -> "52 %"
window.dccFunctions = window.dccFunctions || {};
window.dccFunctions.pctFormat = function (value) { return Math.round(value * 100) + "%"; };
