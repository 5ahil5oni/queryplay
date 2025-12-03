QueryPlay: CSV to SQL Studio

https://queryplay-experiment-query-visualize.streamlit.app/

QueryPlay is a powerful, browser-based data engineering tool that turns your static CSV files into a fully queryable relational database.
Upload multiple datasets, perform complex SQL operations (like JOIN, UNION, GROUP BY), and visualize the results instantly—all without installing a database engine.

🌟 Live Demo

Try it now: https://queryplay-experiment-query-visualize.streamlit.app/

⚡ Key Features

📂 Multi-File Support: Upload multiple CSVs simultaneously. Each file becomes a separate SQL table.
🔗 Advanced SQL: Run standard SQLite queries including Joins across different files.
🧠 Auto-Schema: Automatically detects data types (Numbers, Dates, Strings) and cleans column names (e.g., Order Date 
→
→
 Order_Date).

📊 Instant Visualizations: Generate Bar, Line, Scatter, and Pie charts directly from your query results.
🔒 Privacy First: Runs entirely in-memory. Data is never saved to a disk and is wiped instantly when you refresh or close the tab.
📥 Export: Download your clean results to CSV or Excel.
🛠️ Local Development

If you prefer to run this offline on your own machine:

Clone the repository
Install dependencies:
pip install -r requirements.txt
Run the app:
python -m streamlit run app.py

📦 Tech Stack

Frontend: Streamlit
Engine: Python + Pandas + SQLite3
Charts: Plotly Express
Export: XlsxWriter
Built with ❤️ using Python.
