# 📊 Comprehensive Expense Manager

A resilient, cloud-connected data application built with **Streamlit** and **Pandas**. This tool allows users to upload raw, messy financial CSVs and instantly generates a cleaned, multi-currency normalized, and highly interactive analytical dashboard.

## ✨ Key Features

* **🕵️‍♂️ Dynamic Column Detection:** Automatically scans uploaded CSVs and classifies columns into Temporal (Dates), Numeric (Amounts), and Categorical (Text) data using a 50%+ threshold heuristic.
* **🛡️ Defensive Data Pipeline:** Built to handle real-world "dirty" data. Automatically resolves:
  * Mixed encodings (UTF-8 and Latin-1)
  * European delimiters (semicolons vs. commas)
  * Trailing whitespaces and inconsistent casing
  * Text-wrapped numbers (e.g., `$1,200.50` -> `1200.50`)
* **💱 Live Currency Normalization:** Connects to the Exchange Rate API to normalize mixed currencies (`$`, `€`, `£`, `¥`, `₹`) into a base USD value in real-time. Includes user-defined fallbacks for unlabelled data.
* **📈 Advanced Analytics Engine:** Go beyond standard sums. Calculate Mean, Median, Variance, Standard Deviation, Max/Min, and Volume across categorical and time-series data.
* **💾 Cleaned Data Export:** Download the fully processed, ISO-formatted, and normalized dataset directly from the UI.
* **🎨 Premium UI/UX:** Custom CSS injection and global theming remove boilerplate elements and provide a sleek, dark-mode SaaS aesthetic.

## 🛠️ Technology Stack

* **Frontend/Framework:** [Streamlit](https://streamlit.io/)
* **Data Processing:** [Pandas](https://pandas.pydata.org/)
* **API Integration:** Python `requests` (Open Exchange Rates)
* **Deployment:** Streamlit Community Cloud

## 🚀 Local Installation

To run this project locally on your machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/expense-manager-pro.git](https://github.com/YOUR_USERNAME/expense-manager-pro.git)
   cd expense-manager-pro

2. Create a virtual environment (Optional but recommended):
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

3. Install the dependencies:
   pip install -r requirements.txt

4. Launch the app:
   streamlit run app.py

📂 Project Structure
expense-manager-pro/
│
├── .streamlit/
│   └── config.toml       # Global theme configuration (Dark Mode)
│
├── app.py                # Main application logic and UI routing
├── requirements.txt      # Python dependencies
├── .gitignore            # Git exclusion rules
└── README.md             # Project documentation
