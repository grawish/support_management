import frappe

def before_save(doc, method):
    if len(doc.custom_visits) > 0:
        doc.custom_no_of_man_days = len(doc.custom_visits)
        total_expenses = 0
        for visit in doc.custom_visits:
            total_expenses += visit.total_expenses
        doc.custom_total_expenses = total_expenses
