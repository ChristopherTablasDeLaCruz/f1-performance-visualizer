# F1 Race Dashboard

Interactive dashboard for analyzing Formula 1 race data. Built with Streamlit and FastF1.

## Demo

![Preview of the F1 Race Dashboard](assets/f1-race-dashboard-demo-vid-2x.gif)

*Above: quick GIF preview. same content as youtube video, just lower quality.*

[Watch the full demo on YouTube (2× speed, ~50s)](https://youtu.be/Vw6mTDXLyD0)  
[Try the live app here](https://f1-race-dashboard.streamlit.app/)

## What it does

Lets you explore F1 race data through a web interface. Pick any race from 2018-present and see:

- Race results and fastest lap
- How drivers performed vs their qualifying times  
- Tire strategy timeline
- Individual driver lap time analysis
- Position changes throughout the race
- Telemetry comparison (speed, throttle, braking)

## Why I built this

I wanted to understand F1 strategy better than what you get from just watching races. The official timing data has tons of insights buried in it, but it's not easy to visualize. This dashboard makes it accessible.

## Setup

```bash
git clone [your-repo-url]
cd f1-race-dashboard  
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501

## How it works

- **Data**: FastF1 library pulls from official F1 timing API
- **UI**: Streamlit for the web interface, Plotly for interactive charts
- **Analysis**: Custom logic for comparing qualifying vs race performance


### Pit stop detection
The tricky part was accurately detecting pit stops. Initially used a "laps 20% slower than fastest = pit stop" approach, but this failed badly in races with safety cars or weather changes (Australian GP 2025 showed 17 "pit stops" initially).

Switched to using FastF1's stint data instead - much more reliable since it tracks actual tire changes.


### Code organization
```bash
src/
├── core/
│   └── performance_analyzer.py # Qualifying vs race analysis
├── visualizers/
│   ├── lap_time_charts.py     # Individual driver analysis
│   ├── performance_charts.py  # Driver comparison charts
│   ├── strategy_charts.py     # Tire strategy timeline
│   ├── position_charts.py     # Position change visualization
│   └── telemetry_charts.py    # Car data comparison
└── utils/
    └── race_summary.py        # Race highlight extraction
```


## Future ideas

- Championship standings analysis
- Weather impact correlation
- Lap time prediction models
- Team strategy comparison

## Tech stack

Python, Streamlit, FastF1, Plotly, Pandas

Built this over a few weeks to learn more about F1 strategy and practice building data dashboards.
