#!/usr/bin/env python3
import time
import json
import yfinance as yf
from flask import Flask, Response, render_template_string

app = Flask(__name__)

TICKERS = [
    "^GSPC",     # S&P 500 (US)
    "^DJI",      # Dow Jones Industrial Average (US)
    "^IXIC",     # Nasdaq Composite (US)
    "^RUT",      # Russell 2000 (US small-cap)
    "^FTSE",     # FTSE 100 (UK)
    "^GDAXI",    # DAX (Germany)
    "^FCHI",     # CAC 40 (France)
    "^N225",     # Nikkei 225 (Japan)
    "^HSI",      # Hang Seng (Hong Kong)
    "^AXJO",     # ASX 200 (Australia)
    "^BVSP",     # Bovespa (Brazil)
    "BTC-USD",   # Bitcoin (Crypto)
    "ETH-USD",   # Ethereum (Crypto)
    "GC=F",      # Gold Futures
    "CL=F",      # Crude Oil Futures
    "EURUSD=X",  # EUR/USD currency pair
    "USDJPY=X",  # USD/JPY currency pair
    "AAPL",      # Apple (US)
    "BABA",      # Alibaba (US-listed, China)
    "NESN.SW",   # Nestlé (Switzerland)
    "005930.KS", # Samsung Electronics (South Korea)
    "RIO.AX",    # Rio Tinto (Australia)
    "RELIANCE.NS",# Reliance Industries (India)
    "PBR",       # Petrobras (Brazil)
    "7203.T"     # Toyota (Japan)
]

# One-sentence fallback descriptions
FALLBACK_DESCRIPTIONS = {
    "^GSPC": "A broad measure of the health of the U.S. stock market, reflecting the performance of many large American companies.",
    "^DJI": "A leading barometer of U.S. blue-chip stocks, indicating overall American corporate strength and economic sentiment.",
    "^IXIC": "A benchmark heavily weighted towards technology and growth companies, reflecting the future of the U.S. economy.",
    "^RUT": "A key indicator of small-cap U.S. companies, representing entrepreneurial activity and domestic economic growth.",
    "^FTSE": "A measure of the top 100 companies listed on the London Stock Exchange, signifying global investor confidence in the UK.",
    "^GDAXI": "Germany’s premier stock index, reflecting Europe’s largest economy through its leading global companies.",
    "^FCHI": "France’s primary stock index, offering insight into the broader European market sentiment and stability.",
    "^N225": "Japan’s flagship index, capturing growth and innovation in Asia’s largest developed economy.",
    "^HSI": "Hong Kong’s key stock index, serving as a gateway to China’s economy and Asia’s financial markets.",
    "^AXJO": "Australia’s main benchmark, showing the global commodities impact and economic health of the Pacific region.",
    "^BVSP": "Brazil’s principal index, representing South America’s largest economy and its emerging market potential.",
    "BTC-USD": "The foremost cryptocurrency, symbolizing digital value storage, speculation, and financial innovation.",
    "ETH-USD": "A leading cryptocurrency and smart-contract platform enabling decentralized applications and digital finance.",
    "GC=F": "A global price reference for gold, often seen as a safe-haven asset during times of uncertainty.",
    "CL=F": "A key benchmark for crude oil, shaping energy markets and influencing economic stability worldwide.",
    "EURUSD=X": "The most traded currency pair, reflecting economic dynamics between the Eurozone and the United States.",
    "USDJPY=X": "A major currency pair indicating the interplay between the world’s largest and third-largest economies.",
    "AAPL": "A global leader in consumer electronics and technology, influencing consumer behavior and supply chains.",
    "BABA": "A Chinese e-commerce and tech giant, driving global online retail and digital payments innovation.",
    "NESN.SW": "The world’s largest food and beverage company, influencing global consumer tastes and nutrition trends.",
    "005930.KS": "A key player in electronics and semiconductors, powering global tech ecosystems and digital transformation.",
    "RIO.AX": "A major mining corporation supplying essential raw materials, underpinning global industrial growth.",
    "RELIANCE.NS": "An Indian conglomerate shaping energy, petrochemicals, and telecommunications across emerging markets.",
    "PBR": "Brazil’s leading energy producer, pivotal to Latin America’s oil supply and economic development.",
    "7203.T": "One of the world’s largest automakers, driving innovation and mobility solutions around the globe."
}

TICKER_INFO = {}
for tk in TICKERS:
    t = yf.Ticker(tk)
    try:
        ticker_info = t.info
    except:
        ticker_info = {}
    long_name = ticker_info.get("longName") or ticker_info.get("shortName") or tk
    summary = ticker_info.get("longBusinessSummary")
    if not summary or summary.strip() == "":
        # Use fallback description if none is available
        summary = FALLBACK_DESCRIPTIONS.get(tk, "No description available.")
    TICKER_INFO[tk] = {
        "longName": long_name,
        "description": summary
    }

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MarketStream</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
body {
    background: #0f0f0f;
    color: #0ff;
    margin: 0;
    font-family: 'Press Start 2P', monospace;
    overflow-y: scroll;
}
header {
    text-align: center;
    padding: 20px;
    font-size: 1.5em;
    color: #0ff;
    background: linear-gradient(45deg, #000033, #330033);
    border-bottom: 2px solid #0ff;
    text-shadow: 0 0 5px #0ff, 0 0 10px #0ff;
}
.chart-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    grid-gap: 20px;
    padding: 20px;
}
.chart-box {
    background: #1a1a1a;
    padding: 10px;
    border-radius: 8px;
    box-shadow: 0 0 10px #00ffff33;
    position: relative;
    overflow: hidden;
}
.chart-box h2 {
    font-size: 0.9em;
    text-align: center;
    color: #0ff;
    margin: 0 0 10px 0;
    text-shadow: 0 0 3px #0ff;
    cursor: pointer;
    display: flex;
    justify-content: center;
    gap: 10px;
}
.chart-box h2 span.value {
    font-size: 0.9em;
    text-align: center;
}

/* Tooltip styling */
#tooltip {
    position: absolute;
    background: #111;
    color: #0ff;
    padding: 10px;
    border-radius: 5px;
    font-size: 0.7em;
    line-height: 1.4em;
    box-shadow: 0 0 5px #0ff;
    pointer-events: none;
    z-index: 9999;
    display: none;
    width: 180px;
}
footer {
    text-align: center;
    padding: 20px;
    font-size: 0.7em;
    color: #0ff;
    background: linear-gradient(45deg, #330033, #000033);
    border-top: 2px solid #0ff;
    text-shadow: 0 0 5px #0ff;
}
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: #000;
}
::-webkit-scrollbar-thumb {
    background: #0ff;
}
</style>
</head>
<body>
<header>🚀 MARKET_STREAM 🚀</header>

<div class="chart-container" id="charts-container"></div>

<div id="tooltip"></div>

<footer>AD ASTER PER ASPERA</footer>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const TICKERS = {{tickers_json|safe}};
const TICKER_INFO = {{ticker_info_json|safe}};

const maxDataPoints = 60;

// We'll store data arrays and charts in JS objects keyed by ticker
const dataStore = {};
const charts = {};

// Dimensions/margins for each chart
const margin = {top: 10, right: 50, bottom: 20, left: 40};

// Tooltip element
const tooltip = d3.select('#tooltip');

function createChartContainer(ticker) {
    const container = d3.select('#charts-container')
        .append('div')
        .attr('class', 'chart-box');

    const title = container.append('h2');
    title.append('span').attr('class', 'ticker-symbol').text(ticker);
    const valueSpan = title.append('span').attr('class', 'value').text('—');

    title.on('mouseover', (event) => {
            const info = TICKER_INFO[ticker];
            showTooltip(event, `<strong>${info.longName}</strong><br>${info.description}`);
        })
        .on('mousemove', (event) => {
            moveTooltip(event);
        })
        .on('mouseout', () => {
            hideTooltip();
        });

    const width = 350 - margin.left - margin.right;
    const height = 200 - margin.top - margin.bottom;

    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Price scales and line
    const x = d3.scaleTime().range([0, width]);
    const y = d3.scaleLinear().range([height, 0]);

    // Volume scale (right axis)
    const yVolume = d3.scaleLinear().range([height, 0]);

    // Line generator for price
    const line = d3.line()
        .x(d => x(d.time))
        .y(d => y(d.value));

    // Volume bars group
    const volumeGroup = g.append('g').attr('class', 'volume-bars');

    // Add path for price
    const path = g.append('path')
        .attr('fill', 'none')
        .attr('stroke', '#0ff')
        .attr('stroke-width', 2);

    // Axes groups
    const xAxisGroup = g.append('g')
        .attr('transform', `translate(0,${height})`)
        .attr('color', '#0ff')
        .attr('font-size', '8px');

    const yAxisGroup = g.append('g')
        .attr('color', '#0ff')
        .attr('font-size', '8px');

    // Volume axis on the right
    const yVolumeAxisGroup = g.append('g')
        .attr('transform', `translate(${width},0)`)
        .attr('color', '#0ff')
        .attr('font-size', '8px');

    // Focus elements for tooltip on hover
    const focusLine = g.append('line')
        .attr('class', 'focus-line')
        .attr('stroke', '#0ff')
        .attr('stroke-dasharray', '3,3')
        .attr('y1', 0)
        .attr('y2', height)
        .style('display', 'none');

    const focusCircle = g.append('circle')
        .attr('r', 3)
        .attr('fill', '#0ff')
        .style('display', 'none');

    // Overlay for mouse events
    const overlay = g.append('rect')
        .attr('class', 'overlay')
        .attr('width', width)
        .attr('height', height)
        .attr('fill', 'none')
        .attr('pointer-events', 'all')
        .on('mouseover', () => {
            focusLine.style('display', null);
            focusCircle.style('display', null);
        })
        .on('mouseout', () => {
            hideTooltip();
            focusLine.style('display', 'none');
            focusCircle.style('display', 'none');
        })
        .on('mousemove', event => {
            const d = dataStore[ticker];
            if (!d || d.length === 0) return;
            const mouseX = d3.pointer(event, this)[0];
            const xPos = d3.pointer(event, g.node())[0];
            const x0 = x.invert(xPos);

            // Find the closest data point
            const bisect = d3.bisector(d => d.time).left;
            const i = bisect(d, x0, 1);
            const d0 = d[i - 1];
            const d1 = d[i];
            const closest = !d1 ? d0 : (x0 - d0.time > d1.time - x0 ? d1 : d0);

            // Update focus elements
            focusLine.attr('x1', x(closest.time))
                     .attr('x2', x(closest.time));
            focusCircle.attr('cx', x(closest.time))
                       .attr('cy', y(closest.value));

            showTooltip(event, `Time: ${closest.time.toLocaleTimeString()}<br>Price: ${closest.value.toFixed(2)}<br>Volume: ${closest.volume}`);
            moveTooltip(event);
        });

    charts[ticker] = {
        svg: svg,
        g: g,
        x, y, yVolume, line, path,
        xAxisGroup, yAxisGroup,
        yVolumeAxisGroup,
        volumeGroup,
        width, height,
        valueSpan: valueSpan,
        lastVal: null
    };
}

function updateChart(ticker) {
    const chart = charts[ticker];
    const d = dataStore[ticker];
    if (!d || d.length === 0) return;

    const {x, y, line, path, xAxisGroup, yAxisGroup, width, height, yVolume, yVolumeAxisGroup, volumeGroup} = chart;

    // Extract time, price, and volume arrays
    const times = d.map(pt => pt.time);
    const values = d.map(pt => pt.value);
    const volumes = d.map(pt => pt.volume);

    // Update X domain
    x.domain(d3.extent(times));

    // Update Y (price) domain
    const minVal = d3.min(values);
    const maxVal = d3.max(values);
    let lowerBound = minVal;
    let upperBound = maxVal;
    if (Math.abs(maxVal - minVal) < 1e-8) {
        lowerBound = minVal - (minVal * 0.005);
        upperBound = maxVal + (maxVal * 0.005);
    } else {
        const range = maxVal - minVal;
        lowerBound = minVal - range * 0.05;
        upperBound = maxVal + range * 0.05;
    }
    y.domain([lowerBound, upperBound]);

    // Update line path (price)
    path.datum(d).attr('d', line);

    // Compute min and max volumes
    const minVol = d3.min(volumes) || 0;
    const maxVol = d3.max(volumes) || 0;

    let volLowerBound, volUpperBound;

    if (maxVol <= 0) {
        // If there's no volume data or all zeros, just set a small upper bound
        volLowerBound = 0;
        volUpperBound = 1;
    } else {
        // Normal scaling with padding
        const volRange = maxVol - minVol;
        if (Math.abs(volRange) < 1e-8) {
            volLowerBound = Math.max(0, minVol - (minVol * 0.005));
            volUpperBound = maxVol + (maxVol * 0.005);
        } else {
            volLowerBound = Math.max(0, minVol - volRange * 0.05);
            volUpperBound = maxVol + volRange * 0.05;
        }
    }

    yVolume.domain([volLowerBound, volUpperBound]);

    // When drawing bars
    const bars = volumeGroup.selectAll('rect').data(d);
    const barWidth = width / maxDataPoints * 0.8;
    bars.enter().append('rect')
        .merge(bars)
        .attr('x', pt => x(pt.time) - barWidth/2)
        .attr('y', pt => yVolume(pt.volume))
        .attr('width', barWidth)
        .attr('height', pt => height - yVolume(pt.volume))
        .attr('fill', 'rgba(0,255,255,0.3)');

    bars.exit().remove();

    // Update axes
    const xAxis = d3.axisBottom(x).ticks(5).tickSize(-height).tickFormat(d3.timeFormat('%H:%M:%S'));
    const yAxis = d3.axisLeft(y).ticks(5).tickSize(-width);
    const yVolumeAxis = d3.axisRight(yVolume).ticks(5).tickSize(-width);

    xAxisGroup.call(xAxis)
        .selectAll('line')
        .attr('stroke', '#333');
    xAxisGroup.selectAll('path').attr('stroke', '#333');
    xAxisGroup.selectAll('text').attr('fill', '#0ff');

    yAxisGroup.call(yAxis)
        .selectAll('line')
        .attr('stroke', '#333');
    yAxisGroup.selectAll('path').attr('stroke', '#333');
    yAxisGroup.selectAll('text').attr('fill', '#0ff');

    yVolumeAxisGroup.call(yVolumeAxis)
        .selectAll('line')
        .attr('stroke', '#333');
    yVolumeAxisGroup.selectAll('path').attr('stroke', '#333');
    yVolumeAxisGroup.selectAll('text').attr('fill', '#0ff');
}

// Tooltip functions
function showTooltip(event, html) {
    tooltip.style('display', 'block').html(html);
}
function moveTooltip(event) {
    const [mx, my] = d3.pointer(event);
    tooltip.style('left', (mx + 40) + 'px')
           .style('top', (my + window.scrollY + 20) + 'px');
}
function hideTooltip() {
    tooltip.style('display', 'none');
}

// Initialize all charts
TICKERS.forEach(ticker => {
    dataStore[ticker] = [];
    createChartContainer(ticker);
});

function addDataPoint(ticker, price, cumulativeVolume) {
    const now = new Date();
    const data = dataStore[ticker];

    let intervalVolume = 0;
    if (data.length > 0) {
        const lastEntry = data[data.length - 1];
        intervalVolume = cumulativeVolume - lastEntry.cumulativeVolume;
    } else {
        // For the first data point, there's no previous volume.
        // We'll just set intervalVolume to 0 or cumulativeVolume as is.
        intervalVolume = 0;
    }

    data.push({
        time: now,
        value: +price,
        volume: intervalVolume,            // Store the calculated interval volume
        cumulativeVolume: cumulativeVolume // Keep track of the cumulative volume
    });

    if (data.length > maxDataPoints) {
        data.shift();
    }

    // Update the chart with the intervalVolume instead of cumulativeVolume
    updateChart(ticker);

    // Update displayed last value and color (unchanged)
    const chart = charts[ticker];
    const prevVal = chart.lastVal;
    chart.lastVal = price;
    chart.valueSpan.text(price.toFixed(2));

    if (prevVal !== null) {
        if (price > prevVal) {
            chart.valueSpan.style("color", "limegreen");
        } else if (price < prevVal) {
            chart.valueSpan.style("color", "red");
        } else {
            chart.valueSpan.style("color", "#0ff");
        }
    } else {
        chart.valueSpan.style("color", "#0ff");
    }
}

// SSE for real-time data
const evtSource = new EventSource('/stream');
evtSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    for (const ticker in data) {
        if (charts[ticker]) {
            const val = data[ticker].price;
            const vol = data[ticker].volume;
            if (val !== "N/A") {
                addDataPoint(ticker, +val, +vol);
            }
        }
    }
};
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE,
                                  tickers_json=json.dumps(TICKERS),
                                  ticker_info_json=json.dumps(TICKER_INFO))

@app.route("/stream")
def stream():
    def fetch_price_and_volume(ticker):
        t = yf.Ticker(ticker)
        price = None
        volume = None
        # Attempt fast_info for price and volume
        try:
            price = t.fast_info.last_price
            volume = t.fast_info.last_volume
        except:
            pass
        # If no fast_info volume, try info
        if volume is None:
            try:
                info = t.info
                volume = info.get("regularMarketVolume", 0)
            except:
                volume = 0
        if price is None:
            try:
                info = t.info
                price = info.get("regularMarketPrice")
            except:
                price = None

        print(f"{ticker}: {price}, {volume}")
        return price, volume

    def event_stream():
        while True:
            data = {}
            for tk in TICKERS:
                val, vol = fetch_price_and_volume(tk)
                if val is not None:
                    data[tk] = {"price": val, "volume": vol if vol is not None else 0}
                else:
                    data[tk] = {"price":"N/A", "volume":0}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(10)  # Update every 10 seconds
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True)
