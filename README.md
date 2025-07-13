# COVID-19 Italy Regional Data Dashboard

A modern Flask web application for visualizing COVID-19 epidemiological data from Italian regions, sourced from the Italian Civil Protection Department's official repository.

## 🚀 Features

- **Real-time Data Visualization**: Interactive dashboard with regional COVID-19 statistics
- **Historical Data Search**: Browse data from February 24, 2020 onwards
- **Excel Export**: Generate formatted Excel reports
- **Intelligent Caching**: Smart caching system minimizing API calls
- **Interactive Table Sorting**: Client-side sorting by region, cases, or provinces
- **RESTful API**: JSON endpoints for programmatic access
- **Responsive Design**: Mobile-first design with Tailwind CSS

## 🏗️ Tech Stack

- **Backend**: Flask 3.1.1 + SQLAlchemy
- **Frontend**: Tailwind CSS + Vanilla JavaScript  
- **Database**: SQLite (configurable for PostgreSQL/MySQL)
- **Export**: OpenPyXL for Excel generation
- **HTTP Client**: Requests library

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- [uv](https://docs.astral.sh/uv/) or pip

### Quick Start

**Clone repository**
```bash
git clone <repository-url>
cd covid19-italy-dashboard
```

**Install dependencies**

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -r requirements.txt
```

**Configure environment**
```bash
cp .env.template .env
# Edit .env with your settings (optional for development)
```

**Run application**

Using uv:
```bash
uv run python app.py
```

Using pip:
```bash
python app.py
```

**Access application**
- Open browser to `http://localhost:5000`

## ⚙️ Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | `sqlite:///covid19_italy.db` |
| `DATA_CACHE_MINUTES` | Cache validity | `60` |
| `DEBUG` | Debug mode | `True` |
| `PORT` | Application port | `5000` |

See `.env.template` for all options.

## 📊 Usage

### Web Interface
- **Homepage**: Latest COVID-19 statistics
- **Date Search**: Use date picker for historical data
- **Excel Export**: Click "Excel" button for reports
- **Sorting**: Click column headers to sort

### API Endpoints

**Get regional data**
```http
GET /api/regions?date=2023-01-15&limit=10
```

**Get specific region**
```http
GET /api/regions/lombardia
```

**Excel export**
```http
GET /api/export/excel?date=latest
```

**Response format**
```json
{
  "success": true,
  "data": [
    {
      "region_name": "Lombardia",
      "total_cases": 1250000,
      "provinces_count": 12,
      "last_updated": "2023-01-15 18:30:00"
    }
  ],
  "metadata": {
    "total_regions": 20,
    "total_cases": 8500000
  }
}
```

## 🧠 Caching System

The application implements intelligent caching:

- **Full Cache**: Complete dataset (24h refresh)
- **Latest Cache**: Recent data (60min refresh) 
- **Missing Dates**: Tracks unavailable dates
- **Smart Strategy**: Auto-determines optimal refresh approach
- **Activity-Based**: Reduces frequency when users inactive

## 🚀 Production Deployment

**Environment setup**
```bash
export FLASK_ENV=production
export DEBUG=False
export SECRET_KEY="secure-secret-key"
export DATABASE_URL="postgresql://user:pass@host:5432/db"
```

**Using Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

**Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🔒 Security & Performance

**Security Features**
- Input validation and XSS protection
- SQL injection prevention via SQLAlchemy ORM

**Performance Optimizations**
- Database indexing on key columns
- Bulk operations for large datasets
- Client-side caching and lazy loading

## 📁 Project Structure

```
├── app.py                 # Application entry point
├── config.py             # Configuration management
├── models/               # SQLAlchemy models
├── routes/               # Flask blueprints (main, api)
├── services/             # Business logic (data, cache, export)
├── utils/                # Helper functions
├── static/js/            # Frontend JavaScript
└── templates/            # Jinja2 templates
```

## 📄 Data Source

- **Source**: [Italian Civil Protection Department](https://github.com/pcm-dpc/COVID-19)
- **License**: Creative Commons CC BY 4.0
- **Updates**: Daily at 18:30 CET
- **Coverage**: February 24, 2020 onwards

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push branch (`git push origin feature/name`)
5. Open Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Production-ready Flask application for COVID-19 data visualization**