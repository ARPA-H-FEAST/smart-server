from users.models import User

users = {
    0: {
        "username": "mazumderlab@gwu.edu",
        "email": "mazumderlab@gwu.edu",
        "password": "SampleUser",
        "first_name": "Sample",
        "last_name": "User",
        "access_group_list": ["GW", "NBCC"],
    },
    1: {  # Patient
        "username": "p@p.p",
        "email": "p@p.p",
        "password": "p",
        "first_name": "p",
        "last_name": "p",
        "access_group_list": ["GW", "NBCC"],
    },
    2: {  # Clinician
        "username": "c@c.c",
        "email": "c@c.c",
        "password": "c",
        "first_name": "c",
        "last_name": "c",
        "access_group_list": ["GW", "NBCC"],
    },
    3: {  # Researcher
        "username": "r@r.r",
        "email": "r@r.r",
        "password": "r",
        "first_name": "r",
        "last_name": "r",
        "is_staff": True,
        "access_group_list": ["GW", "NBCC"],
    },
    4: {  # Admin + superuser
        "username": "a",
        "email": "a",
        "password": "a",
        "first_name": "a",
        "last_name": "a",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
    5: {  # For the sake of demonstration
        "username": "rajamazumder@gwu.edu",
        "email": "rajamazumder@gwu.edu",
        "password": "pass123!",
        "first_name": "Raja",
        "last_name": "Mazumder",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
    6: {
        "username": "rykahsay@gwu.edu",
        "email": "rykahsay@gwu.edu",
        "password": "pass123!",
        "first_name": "Robel",
        "last_name": "Kahsay",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
    7: {
        "username": "mazumder@gwu.edu",
        "first_name": "Raja",
        "last_name": "Mazumder",
        "email": "mazumder@gwu.edu",
        "password": "pass123!",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
    8: {
        "username": "pmcneely@gwu.edu",
        "first_name": "Patrick",
        "last_name": "McNeely",
        "email": "pmcneely@gwu.edu",
        "password": "pass123!",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
    9: {
        "username": "keeneyjg@gwu.edu",
        "first_name": "Jonathon",
        "last_name": "Keeney",
        "email": "keeneyjg@gwu.edu",
        "password": "pass123!",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
    10: {
        "username": "lorikrammer@gwu.edu",
        "first_name": "Lori",
        "last_name": "Krammer",
        "email": "lorikrammer@gwu.edu",
        "password": "pass123!",
        "is_staff": True,
        "is_superuser": True,
        "access_group_list": ["GW", "NBCC"],
    },
}

categories = [3, 1, 2, 3, 3, 3, 3, 3, 3, 3]

print(f"====\tCreating USERS\t====")

for k, v in users.items():
    user = User.objects.create_user(**users[k])

# user1 = User.objects.create_user(**users[0])
# user1 = User.objects.create(user=user1, category=3)

# user2 = User.objects.create_user(**users[1])
# user2 = User.objects.create(user=user2, category=1)

# user3 = User.objects.create_user(**users[2])
# user3 = User.objects.create(user=user3, category=2)

# user4 = User.objects.create_user(**users[3])
# user4 = User.objects.create(user=user4, category=3)
