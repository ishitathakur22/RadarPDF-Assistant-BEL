@echo off
echo Starting PDF Q&A System...
call conda activate pdf_qa
E:
cd BEL\PDF_QA_System
streamlit run streamlit_app.py
pause