Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d E:\BEL\PDF_QA_System && E:\anaconda\envs\pdf_qa\python.exe -m streamlit run streamlit_app.py --server.fileWatcherType none", 0, False
WScript.Sleep 8000
WshShell.Run "http://localhost:8501"