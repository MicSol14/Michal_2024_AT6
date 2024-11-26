from user_input_validator import UserInputValidator

validator1 = UserInputValidator()
validator2 = UserInputValidator()

input_list1 = ["10", "-5", "abc", "20", "30"]
input_list2 = ["0", "15", "25", "hello", "-10"]

valid_integers1 = validator1.validate_positive_integers(input_list1)
print("Valid integers from input_list1:", valid_integers1)

valid_integers2 = validator2.validate_positive_integers(input_list2)
print("Valid integers from input_list2:", valid_integers2)