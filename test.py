# import hashlib

# salt = 'abcdef'

# password = 'qpalzm'

# new = password + salt

# print(hashlib.sha256(new.encode()).hexdigest())

import pickle
pickle.dump([], open(r'Data\enrollment.bin','wb'))
pickle.dump([], open(r'Data\face_features.bin','wb'))
