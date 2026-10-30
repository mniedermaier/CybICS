"""
Challenge check: the student recovered FUXA's administrator login (password_attack).

The student brute-forces FUXA's JSON login (POST /api/signin on
172.18.0.4:1881) and enters the user name and password that worked. The
flag used to be text on FUXA's admin-only "Flag" view, but FUXA sends its
whole project, every view included, to anyone without a login
(GET /api/project), so the text was readable without any password. The view
now only says that the admin login works, and the flag comes from here.

The answer is graded against the credentials CybICS ships with
(software/FUXA/README.md), not against the running FUXA: the defence
challenge "Harden FUXA Credentials" has students change that password, and the
attack challenge must stay solvable afterwards. The check does not touch the
stack. Grading is all or nothing (grade()'s default).
"""
import hmac

from modules.defense_checks._answers import grade, one_of

USERNAME = "admin"
PASSWORD = "123456"

LABELS = {"username": "FUXA user name", "password": "Password"}


def verify(answers=None):
    # Passwords are case-sensitive, so the password is compared exactly
    # (one_of() ignores case); the user name is not.
    return grade(answers, {
        "username": one_of(USERNAME),
        "password": lambda value: hmac.compare_digest(value.encode("utf-8"), PASSWORD.encode("utf-8")),
    }, labels=LABELS,
        success_message="That is FUXA's administrator login. A six-digit default password "
                        "falls to the first lines of any wordlist.",
        failure_message="That is not the login of FUXA's administrator account.")
