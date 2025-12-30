from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

print(pwd_context.hash("Admin%1234#"))
# print(pwd_context.hash("User%1234#"))
