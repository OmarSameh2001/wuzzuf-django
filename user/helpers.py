from datetime import datetime

def extract_dob_from_national_id(nat_id):
    if len(nat_id) < 7 or not nat_id.isdigit():
        return None
    
    century_digit = nat_id[0]
    year = int(nat_id[1:3])
    month = int(nat_id[3:5])
    day = int(nat_id[5:7])

    if century_digit == '2':
        year += 1900
    elif century_digit == '3':
        year += 2000
    else:
        return None  # Invalid century

    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None  # Invalid date

