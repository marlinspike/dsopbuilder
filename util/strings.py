
def validate_dsop_rg(rg:str) -> bool:
    '''
        Validates that the Azure Resource group name passed dosen't contain illegal characters
    '''
    is_valid = True
    check_list = ['_','!','@','#','$','%','^','&','*','(',')','`','~',',','.','<','>','?','/']
    if any(s in rg for s in check_list):
        is_valid = False
    return is_valid