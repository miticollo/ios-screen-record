class iPhoneModels:
    MODELS = {
        'iPhone1,1': {'model': 'iPhone', 'width': 547},
        'iPhone1,2': {'model': 'iPhone 3G', 'width': 547},
        'iPhone10,1': {'model': 'iPhone 8 (CDMA)', 'width': 529},                       # 4,7"
        'iPhone10,2': {'model': 'iPhone 8 Plus (CDMA)', 'width': 529},                  # 5,5"
        'iPhone10,3': {'model': 'iPhone X (CDMA)', 'width': 435},                       # 5,8"
        'iPhone10,4': {'model': 'iPhone 8 (GSM)', 'width': 529},                        # 4,7"
        'iPhone10,5': {'model': 'iPhone 8 Plus (GSM)', 'width': 529},                   # 5,5"
        'iPhone10,6': {'model': 'iPhone X (GSM)', 'width': 435},                        # 5,8"
        'iPhone11,2': {'model': 'iPhone XS', 'width': 435},                             # 5,8"
        'iPhone11,4': {'model': 'iPhone XS Max (China mainland)', 'width': 547},
        'iPhone11,6': {'model': 'iPhone XS Max', 'width': 547},
        'iPhone11,8': {'model': 'iPhone XR', 'width': 435},                             # 6,1"
        'iPhone12,1': {'model': 'iPhone 11', 'width': 435},                             # 6,1"
        'iPhone12,3': {'model': 'iPhone 11 Pro', 'width': 435},                         # 5,8"
        'iPhone12,5': {'model': 'iPhone 11 Pro Max', 'width': 547},
        'iPhone12,8': {'model': 'iPhone SE (2nd generation)', 'width': 529},            # 4,7"
        'iPhone13,1': {'model': 'iPhone 12 mini', 'width': 547},
        'iPhone13,2': {'model': 'iPhone 12', 'width': 435},                             # 6,1"
        'iPhone13,3': {'model': 'iPhone 12 Pro', 'width': 435},                         # 6,1"
        'iPhone13,4': {'model': 'iPhone 12 Pro Max', 'width': 547},
        'iPhone14,2': {'model': 'iPhone 13 Pro', 'width': 435},                         # 6,1"
        'iPhone14,3': {'model': 'iPhone 13 Pro Max', 'width': 547},
        'iPhone14,4': {'model': 'iPhone 13 mini', 'width': 547},
        'iPhone14,5': {'model': 'iPhone 13', 'width': 435},                             # 6,1"
        'iPhone14,6': {'model': 'iPhone SE (3rd generation)', 'width': 529},            # 4,7"
        'iPhone14,7': {'model': 'iPhone 14', 'width': 435},                             # 6,1"
        'iPhone14,8': {'model': 'iPhone 14 Plus', 'width': 547},
        'iPhone15,2': {'model': 'iPhone 14 Pro', 'width': 435},                         # 6,1"
        'iPhone15,3': {'model': 'iPhone 14 Pro Max', 'width': 547},
        'iPhone15,4': {'model': 'iPhone 15', 'width': 435},                             # 6,1"
        'iPhone15,5': {'model': 'iPhone 15 Plus', 'width': 547},
        'iPhone16,1': {'model': 'iPhone 15 Pro', 'width': 435},                         # 6,1"
        'iPhone16,2': {'model': 'iPhone 15 Pro Max', 'width': 547},
        'iPhone14,1': {'model': 'Unknown iPhone', 'width': 435},                        # probably iPhone 13 (USB-C)
                                                                                        # A15 Chip by aaronp613
        'iPhone14,9': {'model': 'Unknown iPhone', 'width': 547},                        # probably iPhone 13 mini (USB-C)
                                                                                        # A15 Chip by aaronp613
        'iPhone2,1': {'model': 'iPhone 3GS', 'width': 547},
        'iPhone3,1': {'model': 'iPhone 4 (GSM)', 'width': 547},
        'iPhone3,2': {'model': 'iPhone 4 (GSM, 2012)', 'width': 547},
        'iPhone3,3': {'model': 'iPhone 4 (CDMA)', 'width': 547},
        'iPhone4,1': {'model': 'iPhone 4S', 'width': 547},
        'iPhone5,1': {'model': 'iPhone 5 (GSM)', 'width': 525},                         # 4″
        'iPhone5,2': {'model': 'iPhone 5 (CDMA)', 'width': 525},                        # 4″
        'iPhone5,3': {'model': 'iPhone 5c (GSM)', 'width': 525},                        # 4″
        'iPhone5,4': {'model': 'iPhone 5c (CDMA)', 'width': 525},                       # 4″
        'iPhone6,1': {'model': 'iPhone 5s (GSM)', 'width': 525},                        # 4″
        'iPhone6,2': {'model': 'iPhone 5s (CDMA)', 'width': 525},                       # 4″
        'iPhone7,1': {'model': 'iPhone 6 Plus', 'width': 529},                          # 5,5"
        'iPhone7,2': {'model': 'iPhone 6', 'width': 529},                               # 4,7"
        'iPhone8,1': {'model': 'iPhone 6s', 'width': 529},                              # 4,7"
        'iPhone8,2': {'model': 'iPhone 6s Plus', 'width': 529},                         # 5,5"
        'iPhone8,4': {'model': 'iPhone SE (1st generation)', 'width': 525},             # 4″
        'iPhone9,1': {'model': 'iPhone 7 (CDMA)', 'width': 529},                        # 4,7"
        'iPhone9,2': {'model': 'iPhone 7 Plus (CDMA)', 'width': 529},                   # 5,5"
        'iPhone9,3': {'model': 'iPhone 7 (GSM)', 'width': 529},                         # 4,7"
        'iPhone9,4': {'model': 'iPhone 7 Plus (GSM)', 'width': 529},                    # 5,5"
    }

    @staticmethod
    def get_model(key):
        return iPhoneModels.MODELS.get(key, "Unknown model")['model']

    @staticmethod
    def get_width(key):
        return iPhoneModels.MODELS.get(key, "Unknown model")['width']
