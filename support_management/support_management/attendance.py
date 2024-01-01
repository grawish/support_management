import frappe

def validate(doc,method=None):
#     find the time difference between checkin and checkout and save it in total_Duration
    print(doc.as_dict())
    doc.total_duration = 0
    return True
