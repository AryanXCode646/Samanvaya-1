# Samanvaya Makefile: Single-Command Automation

.PHONY: install run dev api test docker clean info help pipeline metrics evaluate verify-raster report-pdf test-ws

PYTHON := python3
PIP := pip

help:
	@echo "Samanvaya: Lunar Optical Image Registration Framework"
	@echo "Usage:"
	@echo "  make dev          - ONE COMMAND: Start all 3 services (ML + Node.js + React)"
	@echo "  make install      - Install dependencies and register 'samanvaya' CLI"
	@echo "  make pipeline     - Run end-to-end lunar registration pipeline with Minnaert correction"
	@echo "  make metrics      - Generate Phase 1 evaluation metrics report (JSON & CSV)"
	@echo "  make verify-raster- Real raster out-of-core windowed tile verification"
	@echo "  make report-pdf   - Generate executive ReportLab PDF mission report"
	@echo "  make test-ws      - Stream live asynchronous WebSocket telemetry"
	@echo "  make run          - Launch interactive Streamlit portal (port 8501)"
	@echo "  make api          - Launch FastAPI REST backend (port 8000)"
	@echo "  make test         - Run full automated verification suite"
	@echo "  make docker       - Build and start Docker container stack"
	@echo "  make clean        - Remove build artifacts and caches"
	@echo "  make info         - Display system environment and mission telemetry"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "✅ Python core installed! Run 'make install-all' to also install Node.js deps."

install-all:
	@echo "📦 Installing all dependencies (Python + Node.js)..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	cd backend && npm install
	cd frontend && npm install
	@echo "✅ All dependencies installed! Run 'make dev' to start."

dev:
	@echo "🌙 Starting Samanvaya Full-Stack (ML + Gateway + React)..."
	@npm start

run:
	@echo "🚀 Launching Samanvaya Web Portal on http://localhost:8501 ..."
	streamlit run lunar_core/ui/app.py --server.port 8501

api:
	@echo "🛰️ Launching Samanvaya REST API on http://localhost:8000 ..."
	uvicorn ch2_lunar_reg.interfaces.api:app --host 0.0.0.0 --port 8000 --reload

test:
	@echo "🧪 Running full automated verification test suite..."
	pytest tests/ ch2_lunar_reg/tests/ -v

pipeline:
	@echo "🛰️ Running end-to-end registration pipeline (Minnaert + Sub-pixel)..."
	$(PYTHON) run_pipeline.py --scenario scenario_a

metrics:
	@echo "📊 Computing evaluation metrics (RMSE, Inlier Ratio, Uniformity)..."
	$(PYTHON) metrics.py

evaluate: metrics

verify-raster:
	@echo "🛰️ Running real raster out-of-core verification harness..."
	$(PYTHON) verify_raster_run.py --scenario scenario_a

report-pdf:
	@echo "📄 Generating executive ReportLab PDF mission report..."
	$(PYTHON) pdf_reporter.py --json evaluation_report.json --output samanvaya_mission_report.pdf

test-ws:
	@echo "🌊 Streaming live asynchronous WebSocket telemetry..."
	$(PYTHON) test_websocket_client.py --in-process

docker:
	@echo "🐳 Building and starting Docker container stack..."
	docker compose up --build

info:
	@$(PYTHON) -m lunar_core.cli info

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[cod]" -delete
	rm -rf tests/temp_* *.tmp *.log
