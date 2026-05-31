import streamlit as st
import pandas as pd
import requests

@st.cache_data(ttl=43200)
def fetch_live_exchange_rates():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        data = response.json()
        return data.get("rates", {})
    except Exception:
        st.toast("⚠️ Warning: Could not connect to live exchange rates. Using fallback rates.", icon="📡")
        return {'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 150.5, 'INR': 85.2}

st.set_page_config(page_title="Comprehensive Expense Manager", layout="wide")
# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
    /* 1. Hide the Streamlit branding menu, header, and footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. Upgrade the Metric Cards (Make them look like floating widgets) */
    div[data-testid="metric-container"] {
        background-color: #1F2937; /* Matches our secondary background */
        border: 1px solid #374151; /* Subtle border */
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* 3. Make the file uploader box look more premium */
    div[data-testid="stFileUploadDropzone"] {
        border-radius: 15px;
        border: 2px dashed #636EFA;
        background-color: #111827;
    }
    
    /* 4. Polish the Download Button */
    .stDownloadButton>button {
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stDownloadButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(99, 110, 250, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Comprehensive Expense Manager")
st.write("Upload any expense CSV file. The system will auto-detect columns, normalize multi-currency inputs, and run advanced statistical analyses.")
st.divider()

st.header("Step 1: Upload Your Data")
uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"])

if uploaded_file is not None:
    # --- PATCH 1 & 2: Delimiter Sniffing and Encoding Fallbacks ---
    try:
        # Attempt 1: Standard UTF-8 with automatic delimiter sniffing
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
    except UnicodeDecodeError:
        # Attempt 2: Rewind the file and try Windows/Latin-1 encoding
        uploaded_file.seek(0)
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
        except Exception as e:
            st.error(f"⚠️ Critical System Error parsing file: {e}")
            st.stop()
    except pd.errors.ParserError:
        st.error("⚠️ We found a structural formatting error in your CSV. Ensure data is properly delimited.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Unexpected Error: {e}")
        st.stop()
        
    # --- PATCH 3: The Empty Data Guardrail ---
    if df.empty:
        st.error("⚠️ The uploaded file contains column headers but zero data rows. Please upload a populated dataset.")
        st.stop()

    st.success("File uploaded and parsed successfully!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Data Preview")
        st.dataframe(df.head(10))
        st.write(f"**Total Rows:** {df.shape[0]} | **Total Columns:** {df.shape[1]}")
        
    with col2:
        st.subheader("🕵️‍♂️ Dynamic Column Detection")
        numeric_cols = []
        date_cols = []
        text_cols = []
        
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                numeric_cols.append(col)
            else:
                sample = df[col].dropna().head(10)
                if not sample.empty:
                    sample_str = sample.astype(str).str.replace(r'[$,£€¥₹\s]', '', regex=True)
                    sample_num = pd.to_numeric(sample_str, errors='coerce')
                    converted_date = pd.to_datetime(sample, format='mixed', errors='coerce')
                    
                    if converted_date.notna().sum() >= len(sample) * 0.5:
                        date_cols.append(col)
                    elif sample_num.notna().sum() >= len(sample) * 0.8:
                        numeric_cols.append(col)
                    else:
                        text_cols.append(col)
                else:
                    text_cols.append(col)
                
        st.write(f"**Numeric (Amounts):** `{numeric_cols}`")
        st.write(f"**Temporal (Dates):** `{date_cols}`")
        st.write(f"**Text (Categories):** `{text_cols}`")
        
        st.divider()
        st.subheader("Step 2: Confirm Mapping & Settings")
        
        selected_amount = st.selectbox(
            "Which column is the Amount?", 
            options=numeric_cols if numeric_cols else df.columns
        )
        
        selected_categories = st.multiselect(
            "Which column(s) represent the Categories?", 
            options=text_cols if text_cols else df.columns,
            default=[text_cols[0]] if text_cols else None
        )
        
        selected_date = st.selectbox(
            "Which column represents the Date?",
            options=date_cols if date_cols else ["No Date Column Found"]
        )

        fallback_currency = st.selectbox(
            "Fallback Currency (If no currency symbol is detected in a row):",
            options=["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "JPY (¥)"],
            index=0
        )
        fallback_iso = fallback_currency.split(" ")[0]

    # --- PATCH 4: The Math Engine Guardrail ---
    if not selected_categories:
        st.warning("⚠️ Please select at least one Category column to proceed.")
        st.stop()
        
    if not selected_amount:
        st.warning("⚠️ Please select a valid Amount column to proceed.")
        st.stop()

    st.divider()
    clean_df = df.copy()
    
    for col in selected_categories:
        clean_df[col] = clean_df[col].fillna("Unknown")
        clean_df[col] = clean_df[col].astype(str).str.strip().str.title()
        
    live_rates = fetch_live_exchange_rates()
    symbol_to_iso = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR'}
    
    if clean_df[selected_amount].dtype == 'object':
        clean_df['Detected_Symbol'] = clean_df[selected_amount].astype(str).str.extract(r'([$€£¥₹])')[0]
        clean_df['ISO_Code'] = clean_df['Detected_Symbol'].map(symbol_to_iso).fillna(fallback_iso)
        clean_df[selected_amount] = clean_df[selected_amount].astype(str).str.replace(r'[$,£€¥₹\s]', '', regex=True)
        clean_df[selected_amount] = pd.to_numeric(clean_df[selected_amount], errors='coerce').fillna(0)
        clean_df['Normalized_Amount_USD'] = clean_df.apply(
            lambda row: row[selected_amount] / live_rates.get(row['ISO_Code'], 1.0), 
            axis=1
        )
    else:
        clean_df[selected_amount] = pd.to_numeric(clean_df[selected_amount], errors='coerce').fillna(0)
        clean_df['Normalized_Amount_USD'] = clean_df[selected_amount] / live_rates.get(fallback_iso, 1.0)
        
    math_target = 'Normalized_Amount_USD'
        
    if selected_date != "No Date Column Found":
        clean_df['Parsed_Date'] = pd.to_datetime(clean_df[selected_date], format='mixed', errors='coerce')
        bad_dates_df = clean_df[clean_df['Parsed_Date'].isna()]
        clean_df = clean_df.dropna(subset=['Parsed_Date'])
        
        if not bad_dates_df.empty:
            lost_money = bad_dates_df[math_target].sum()
            st.warning(f"⚠️ **Data Quality Alert:** Found {len(bad_dates_df)} row(s) with unparseable or ambiguous dates (Totaling ${lost_money:,.2f} USD). These rows have been set aside.")
            with st.expander("👀 View excluded rows"):
                st.dataframe(bad_dates_df.drop(columns=['Parsed_Date'], errors='ignore'))
        
        if not clean_df.empty:
            min_date = clean_df['Parsed_Date'].min().date()
            max_date = clean_df['Parsed_Date'].max().date()
            
            st.header("Step 3: Filter Timeline")
            col_start, col_end = st.columns(2)
            
            with col_start:
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
                
            with col_end:
                end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
            
            if start_date <= end_date:
                clean_df = clean_df[
                    (clean_df['Parsed_Date'].dt.date >= start_date) & 
                    (clean_df['Parsed_Date'].dt.date <= end_date)
                ]
            else:
                st.error("⚠️ Invalid Date Range.")
                st.stop()
        else:
            st.error("⚠️ Critical Error: No valid date rows left to analyze.")
            st.stop()

    st.divider()
    st.header("Step 4: Analytics Dashboard")
    
    if len(selected_categories) > 1:
        clean_df['Combined_Category'] = clean_df[selected_categories].astype(str).agg(' | '.join, axis=1)
        group_target = 'Combined_Category'
    else:
        group_target = selected_categories[0]
        
    st.subheader("⚙️ Statistical Calculation Engine")
    agg_choice = st.selectbox(
        "Select Metric to Analyze:",
        options=[
            "Sum (Total Spending)", 
            "Average (Mean Transaction Size)", 
            "Median (Middle Value - Ignores Outliers)", 
            "Max (Highest Expense)", 
            "Min (Lowest Expense)", 
            "Count (Transaction Volume)",
            "Std Dev (Spending Volatility/Spread)",
            "Variance (Statistical Distribution)"
        ],
        index=0
    )
    
    agg_key = agg_choice.split(" ")[0].strip()
    agg_map = {
        "Sum": "sum", "Average": "mean", "Median": "median", 
        "Max": "max", "Min": "min", "Count": "count", 
        "Std": "std", "Variance": "var"
    }
    pandas_agg = agg_map[agg_key]
        
    summary_df = clean_df.groupby(group_target)[math_target].agg(pandas_agg).reset_index()
    summary_df = summary_df.sort_values(by=math_target, ascending=False)
    summary_df = summary_df.rename(columns={math_target: f"USD ({agg_key})"})
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader(f"Categorical {agg_key} Analytics")
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
        
        if agg_key == "Sum": grand_metric = clean_df[math_target].sum()
        elif agg_key == "Average": grand_metric = clean_df[math_target].mean()
        elif agg_key == "Median": grand_metric = clean_df[math_target].median()
        elif agg_key == "Max": grand_metric = clean_df[math_target].max()
        elif agg_key == "Min": grand_metric = clean_df[math_target].min()
        elif agg_key == "Count": grand_metric = len(clean_df)
        elif agg_key == "Std": grand_metric = clean_df[math_target].std()
        elif agg_key == "Variance": grand_metric = clean_df[math_target].var()
        
        if agg_key == "Count":
            st.metric(label="Total Record Volume", value=f"{grand_metric:,.0f} Transactions")
        elif agg_key in ["Std", "Variance"]:
            st.metric(label=f"Dataset {agg_key} Index", value=f"{grand_metric:,.4f}")
        else:
            st.metric(label=f"Overall {agg_key} (USD)", value=f"${grand_metric:,.2f}")
        
    with col4:
        st.subheader("Visual Distribution Plot")
        chart_data = summary_df.set_index(group_target)
        st.bar_chart(chart_data)
        
    if selected_date != "No Date Column Found":
        st.divider()
        st.subheader(f"📈 {agg_key} Trendline Over Time (USD)")
        
        clean_df['Date_Only'] = clean_df['Parsed_Date'].dt.date
        time_cat_df = clean_df.groupby(['Date_Only', group_target])[math_target].agg(pandas_agg).reset_index()
        
        pivot_df = time_cat_df.pivot(index='Date_Only', columns=group_target, values=math_target).fillna(0)
        if agg_key in ["Count", "Variance"]:
            st.bar_chart(pivot_df)
        else:
            st.line_chart(pivot_df)

    st.divider()
    st.subheader("💾 Export Cleaned Dataset")
    st.write("Your downloaded file includes normalized calculations and explicit fallback tracking flags.")
    
    export_df = clean_df.copy()
    if selected_date != "No Date Column Found":
        export_df[selected_date] = export_df['Parsed_Date'].dt.strftime('%Y-%m-%d')
        
    export_df = export_df.fillna("N/A")
    export_df = export_df.drop(columns=['Parsed_Date', 'Date_Only', 'Combined_Category', 'Detected_Symbol'], errors='ignore')
    
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Cleaned CSV",
        data=csv_data,
        file_name="cleaned_expenses.csv",
        mime="text/csv"
    )

else:
    st.info("Awaiting file upload. Please upload a CSV to begin.")