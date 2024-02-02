import frappe

def on_update(doc, method):
#     set length of visits to no of days in warranty period
    doc.custom_no_of_man_days = len(doc.custom_visits)
    total_expenses = 0
    for visit in doc.custom_visits:
        total_expenses += visit.custom_total_expenses
    doc.custom_total_expenses = total_expenses
