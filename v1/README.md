# Stock Analysis System - Backend + Q&A Architecture

## 🎯 **System Overview**

A clean, efficient stock analysis system with:
- **Backend Service**: Continuous data collection and analysis
- **Single FAISS Database**: All data stored in one common database
- **Q&A Streamlit App**: Simple interface for asking questions
- **No Repeated Analysis**: Analysis happens once, stored permanently

## 📁 **Project Structure**

```
Stock-Bot/
├── backend_service.py              # Backend data collection service
├── qa_app.py                       # Q&A Streamlit app
├── start.py                        # Startup script
├── nova_pro_client.py              # Nova Pro client
├── requirements.txt                # Dependencies
├── .env                           # AWS credentials
├── src/                           # Modular components
│   ├── __init__.py                # Main module entry point
│   ├── data_collector.py          # 5-minute data collection
│   ├── chart_generator.py         # Chart generation
│   ├── excel_reporter.py          # Excel report creation
│   ├── video_creator.py           # Video creation
│   ├── multimodal_analyzer.py     # Nova Pro analysis
│   ├── faiss_builder.py           # FAISS index building
│   └── qa_system.py               # Q&A functionality
├── data/                          # Generated data
│   ├── charts/                    # Generated charts
│   ├── excel/                     # Excel reports
│   ├── videos/                    # Generated videos
│   └── faiss/                     # FAISS database
└── config/                        # Configuration files
```

## 🚀 **How to Use**

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Set AWS Credentials**
Create `.env` file:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 3. **Start Backend Service**
```bash
python3 backend_service.py
```
This will:
- Collect data for AAPL, TSLA, GOOGL (configurable)
- Create Excel reports, charts, videos
- Perform multimodal analysis with Nova Pro
- Build and maintain a single FAISS database
- Update every 30 minutes automatically

### 4. **Start Q&A App**
```bash
streamlit run qa_app.py
```
Access the web interface at `http://localhost:8501`

### 5. **Quick Start**
```bash
python3 start.py
```

## 🔄 **System Architecture**

### **Backend Service (`backend_service.py`)**
- **Continuous Data Collection**: Runs every 30 minutes
- **Multi-Symbol Support**: AAPL, TSLA, GOOGL (configurable)
- **Complete Analysis Pipeline**: Data → Excel → Charts → Video → Nova Pro → FAISS
- **Database Management**: Single FAISS database with merging capability
- **Error Handling**: Robust error handling and logging

### **Q&A App (`qa_app.py`)**
- **Simple Interface**: Clean, focused Q&A interface
- **Quick Questions**: Pre-defined common questions
- **Database Status**: Shows database health and last update
- **Sample Questions**: Guide for users
- **Real-time Answers**: Instant responses from FAISS database

### **Database Structure**
- **Single FAISS Index**: `data/faiss/stock_analysis_db.faiss`
- **Metadata Storage**: `data/faiss/stock_analysis_metadata.pkl`
- **Automatic Merging**: New data merges with existing database
- **Persistent Storage**: Database survives service restarts

## 📊 **Features**

### **Data Collection**
- Real-time 5-minute data collection
- Historical data retrieval (3 days)
- Multi-symbol monitoring
- Automatic data storage

### **Analysis Pipeline**
1. **Data Collection** → 2. **Excel Reports** → 3. **Chart Generation** → 4. **Video Creation** → 5. **Nova Pro Analysis** → 6. **FAISS Database**

### **Q&A Capabilities**
- Ask questions about stock data
- Get answers from FAISS index
- View available topics
- Quick question buttons
- Database status monitoring

## 🔧 **Configuration**

### **Symbols to Monitor**
Edit `backend_service.py`:
```python
symbols = ["AAPL", "TSLA", "GOOGL", "MSFT"]  # Add your symbols
```

### **Update Frequency**
Edit `backend_service.py`:
```python
schedule.every(30).minutes.do(self._update_all_symbols)  # Change frequency
```

### **Database Location**
Edit `backend_service.py`:
```python
self.faiss_db_path = "data/faiss/stock_analysis_db.faiss"
```

## 🎯 **Key Benefits**

1. **Efficient Architecture**: Backend does heavy lifting, frontend is lightweight
2. **Single Database**: All data in one place, easy to manage
3. **Continuous Updates**: Automatic data collection and analysis
4. **No Redundancy**: Analysis happens once, stored permanently
5. **Scalable**: Easy to add more symbols
6. **User-Friendly**: Simple Q&A interface
7. **Robust**: Error handling and recovery

## 🔄 **Workflow**

1. **Backend Service**: Runs continuously, collects data, performs analysis
2. **Database**: Stores all analysis results in FAISS index
3. **Q&A App**: Provides interface for querying the database
4. **User**: Asks questions, gets instant answers

## 📈 **Data Flow**

```
yfinance → 5min data → Excel/Charts/Video → Nova Pro → FAISS → Q&A
```

This system provides a complete, efficient solution for stock analysis with continuous data collection and instant Q&A capabilities.
