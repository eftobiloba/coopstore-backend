from app.routers import products, categories, carts, users, auth, accounts, scraping
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


description = """
Welcome to the CoopStore E-commerce API! 🚀

This API provides a comprehensive set of functionalities for managing the e-commerce platform.

Key features include:

- **Crud**
	- Create, Read, Update, and Delete endpoints.
- **Search**
	- Find specific information with parameters and pagination.
- **Auth**
	- Verify user/system identity.
	- Secure with Access and Refresh tokens.
- **Permission**
	- Assign roles with specific permissions.
	- Different access levels for User/Admin.
- **Validation**
	- Ensure accurate and secure input data.


For any inquiries, please contact:

"""


app = FastAPI(
    description=description,
    title="CoopStore E-commerce APIs",
    version="1.0.0",
    contact={
        "name": "Faseyitan Tobiloba",
        "url": "https://github.com/eftobiloba/coopstore-frontend",
    },
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "layout": "BaseLayout",
        "filter": True,
        "tryItOutEnabled": True,
        "onComplete": "Ok"
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(products.router)
app.include_router(categories.router)
app.include_router(carts.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(auth.router)
app.include_router(scraping.router)