from datetime import datetime
from io import BytesIO

from docx import Document

SECTION_ORDER = [
    ("CONTEXT", "3. Контекст"), ("PROBLEM", "4. Проблема"), ("GOAL", "5. Цель"), ("BUSINESS_EFFECT", "6. Бизнес-эффект"),
    ("AS_IS", "7. AS IS"), ("TO_BE", "8. TO BE"), ("USE_CASES", "9. Use Cases"), ("FUNCTIONAL_REQUIREMENTS", "10. Функциональные требования"),
    ("NON_FUNCTIONAL_REQUIREMENTS", "11. Нефункциональные требования"), ("RISKS", "12. Риски"), ("FINAL_BT", "13. Финальный БТ"),
]

def build_docx(project, artifacts):
    doc = Document()
    doc.add_heading(project.project_name, 0)
    doc.add_paragraph(f"Статус: {project.status}")
    doc.add_paragraph(f"Дата: {datetime.utcnow().strftime('%Y-%m-%d')}")
    doc.add_paragraph("Версия: рабочая")
    doc.add_paragraph("Автор: Александр")
    doc.add_page_break()
    doc.add_heading("2. Содержание", level=1)
    for _, title in SECTION_ORDER:
        doc.add_paragraph(title)
    art = {a.artifact_type.value: a for a in artifacts}
    for key, title in SECTION_ORDER:
        doc.add_page_break(); doc.add_heading(title, level=1)
        a = art.get(key)
        doc.add_paragraph((a.content if a else "") or "Раздел пока не заполнен")
    bio = BytesIO(); doc.save(bio); bio.seek(0)
    return bio
