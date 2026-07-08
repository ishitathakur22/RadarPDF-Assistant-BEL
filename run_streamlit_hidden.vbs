Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d E:\BEL\PDF_QA_System && E:\anaconda\envs\pdf_qa\python.exe -m streamlit run streamlit_app.py", 0, False