def can_convert_to(tipe, value):
    try:
        _ = tipe(value)
        return True
    except:
        return False

