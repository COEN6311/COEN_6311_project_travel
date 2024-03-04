def is_strong_password(password):
    '''Check if the password meets the criteria for a strong password'''
    return (
            len(password) >= 8 and
            any(char.isupper() for char in password) and
            any(char.islower() for char in password) and
            any(char.isdigit() for char in password) and
            any(char in "!@#$%^&*" for char in password)
    )