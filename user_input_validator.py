class UserInputValidator:
    def validate_positive_integers(self, input_list):
        valid_integers = []
        for item in input_list:
            if item.isdigit() and int(item) > 0:
                valid_integers.append(int(item))
        self.display_validation_message()
        return valid_integers

    def display_validation_message(self):
        print("The input list has been validated.")